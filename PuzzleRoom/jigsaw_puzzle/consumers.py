# jigsaw_puzzle/consumers.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import JigsawPuzzlePiece, JigsawPuzzleRoom
from asgiref.sync import async_to_sync
from django.utils import timezone
from .models import ChatMessage
from user.models import User
from . import models
from PIL import Image, ImageChops
import os
from django.conf import settings
from django.shortcuts import get_object_or_404
import logging
logger = logging.getLogger(__name__)

class PuzzleConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_id = self.scope['url_route']['kwargs']['room_id']
        self.room_group_name = f'puzzle_room_{self.room_id}'

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()
        
        # Load and send the current state of the game
        await self.send_current_state()


    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        # Set last active timestamp for the room
        room = await database_sync_to_async(JigsawPuzzleRoom.objects.get)(id=self.room_id)
        room.last_active = timezone.now()
        await database_sync_to_async(room.save)()

    async def player_left(self, event):
        await self.send(text_data=json.dumps({
            "type": "player.left",
            "message": event["message"],
        }))

    async def receive(self, text_data):
        data = json.loads(text_data)
        message_type = data['type']

        if message_type == 'chat_message':
            await self.handle_chat_message(data)
        elif message_type == 'piece_move':
            await self.handle_piece_move(data)
        elif message_type == 'piece_remove':
            await self.handle_piece_remove(data)
        elif message_type == 'player_ready':
            await self.handle_player_ready(data)
        elif message_type == 'piece_lock':
            await self.handle_piece_lock(data)
        elif message_type == 'piece_unlock':
            await self.handle_piece_unlock(data)
        elif message_type == 'check_completion':
            # Check if puzzle is completed after every move
            if await self.is_puzzle_completed():
                await self.mark_puzzle_as_completed()
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'puzzle_completed',
                        'message': 'Puzzle is completed!',
                    }
                )
    
    async def send_current_state(self):
        room = await database_sync_to_async(JigsawPuzzleRoom.objects.get)(id=self.room_id)
        pieces = await database_sync_to_async(list)(
            JigsawPuzzlePiece.objects.filter(room=room).values(
                "id", "x_position", "y_position", "is_placed", "is_correct", "image_piece", "placed_by", "grid_x", "grid_y"
            )
        ) or []

        chat_messages = await database_sync_to_async(list)(
            ChatMessage.objects.filter(room=room).values("user__username", "message")
        ) or []
        elapsed_time = await database_sync_to_async(room.get_elapsed_time)()
        moves_taken = room.moves_taken
    
        # Ensure all piece data is properly formatted
        for piece in pieces:
            if piece["is_placed"]:
                if piece["x_position"] is None or piece["y_position"] is None:
                    logger.error(f" ERROR: Piece {piece['id']} is placed but missing position!")
                # Convert image_piece to URL if it's a FileField
                if piece.get("image_piece"):
                    piece["image_url"] = piece["image_piece"].url if hasattr(piece["image_piece"], 'url') else str(piece["image_piece"])

        await self.send(text_data=json.dumps({
            'type': 'current_state',
            'pieces': pieces,
            'chat_messages': chat_messages,
            'puzzle_completed': room.completed,
            'elapsed_time': elapsed_time,
            'moves_taken': moves_taken,
            'player1_moves': room.player1_moves,
            'player2_moves': room.player2_moves,
        }))

    async def handle_chat_message(self, data):
        message = data['message']
        username = data['username']
        await self.save_chat_message(username, message)
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message,
                'username': username
            }
        )

    async def handle_piece_move(self, data):
        piece_id = data['piece_id']
        new_x = data['new_x']
        new_y = data['new_y']
        player_role = data['player_role']
        base_grid_size = data['base_grid_size']
        print(f"🔍 Piece {piece_id} | New X: {new_x}, New Y: {new_y} | Player: {player_role}")

        image_url = data.get('image_url', None)

        # Get the piece object
        piece = await database_sync_to_async(JigsawPuzzlePiece.objects.get)(id=piece_id)

        # Update piece position in the database
        await self.update_piece_position(piece_id, new_x, new_y, player_role)

        room = await database_sync_to_async(JigsawPuzzleRoom.objects.get)(id=self.room_id)
        if player_role == "player1":
            room.player1_moves += 1
        elif player_role == "player2":
            room.player2_moves += 1
        room.moves_taken += 1  # Increment total moves
        await database_sync_to_async(room.save)()

        elapsed_time = await database_sync_to_async(room.get_elapsed_time)()
        piece_correct = await self.is_piece_correct(piece_id, base_grid_size)

        if piece_correct:
            await self.is_puzzle_completed()
        print(f"Sending piece_move event: player1_moves={room.player1_moves}, player2_moves={room.player2_moves}")
        # Send the updated position to all players in the room
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'piece_move',
                'piece_id': piece_id,
                'new_x': new_x,
                'new_y': new_y,
                'player_role': player_role,
                'image_url': image_url if image_url else (piece.image_piece.url if piece.image_piece and piece.image_piece.name else None),  # ✅ FIXED
                'is_correct': piece.is_correct,
                'moves_taken': room.moves_taken,
                'elapsed_time': elapsed_time,
                'player1_moves': room.player1_moves,  # Send player1's moves
                'player2_moves': room.player2_moves,  # Send player2's moves
        
            }
        )

    async def handle_piece_remove(self, data):
        piece_id = data['piece_id']
        player_role = data.get('player_role')

        # Check if the puzzle is already completed
        room = await database_sync_to_async(JigsawPuzzleRoom.objects.get)(id=self.room_id)
        if room.completed:
            print(f"Cannot remove piece {piece_id}, puzzle is already completed.")
            return  # Stop removal if puzzle is completed

        # Reset the piece in the database
        piece = await database_sync_to_async(JigsawPuzzlePiece.objects.get)(id=piece_id)
        piece.x_position = None
        piece.y_position = None
        piece.is_placed = False
        piece.is_correct = False
        piece.placed_by = None
        piece.locked_by = None
        await database_sync_to_async(piece.save)()

        # Broadcast the removal to all clients
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'piece_remove',
                'piece_id': piece_id,
                'player_role': player_role
            }
        )

    async def puzzle_completed(self, event):
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"📡 Receiving puzzle_completed event: {event}")

        await self.send(text_data=json.dumps({
            'type': 'puzzle_completed',
            'winner': event.get('winner', "Unknown"),  # Make sure 'winner' is included
            'message': event['message'],
            'completion_time': event.get('completion_time', 0),
            'moves_taken': event.get('moves_taken', 0),
        }))



    async def handle_player_ready(self, data):
        player_role = data['player_role']
        is_ready = data['is_ready']
        await self.update_player_ready_status(player_role, is_ready)
        room = await database_sync_to_async(JigsawPuzzleRoom.objects.get)(id=self.room_id)
        
        if room.player1_ready and room.player2_ready:
            if not room.start_time:
                room.start_time = timezone.now()  # ✅ Set game start time here!
                await database_sync_to_async(room.save)()
                logger.info("🕒 Game started, start_time set!")

            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'both_ready',
                }
            )
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'player_ready',
                'player_role': player_role,
                'is_ready': is_ready,
            }
        )
        

        room = await database_sync_to_async(JigsawPuzzleRoom.objects.get)(id=self.room_id)
        if room.player1_ready and room.player2_ready and room.start_time is None:
            room.start_time = timezone.now()
            await database_sync_to_async(room.save)()
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'both_ready',
                }
            )

    async def handle_piece_lock(self, data):
        piece_id = data['piece_id']
        player_role = data['player_role']
        if await self.lock_piece(piece_id, player_role):
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'piece_lock',
                    'piece_id': piece_id,
                    'locked_by': player_role,
                }
            )

    async def handle_piece_unlock(self, data):
        piece_id = data['piece_id']
        if await self.unlock_piece(piece_id):
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'piece_unlock',
                    'piece_id': piece_id,
                }
            )


    @database_sync_to_async
    def save_chat_message(self, username, message):
        room = JigsawPuzzleRoom.objects.get(id=self.room_id)
        user = User.objects.get(username=username)
        ChatMessage.objects.create(room=room, user=user, message=message)

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            'type': 'chat_message',
            'message': event['message'],
            'username': event['username']
        }))

    async def piece_move(self, event):
        await self.send(text_data=json.dumps({
            'type': 'piece_move',
            'piece_id': event['piece_id'],
            'new_x': event['new_x'],
            'new_y': event['new_y'],
            'player_role': event['player_role'],
            'image_url': event['image_url'],  
            'is_correct': event.get('is_correct', False),
            'moves_taken': event.get('moves_taken', 0),
            'elapsed_time': event.get('elapsed_time', 0),
            'player1_moves': event.get('player1_moves', 0),
            'player2_moves': event.get('player2_moves', 0)
        }))

    async def piece_remove(self, event):
        # Send the removal event to all connected clients
        await self.send(text_data=json.dumps({
            'type': 'piece_remove',
            'piece_id': event['piece_id'],
            'player_role': event['player_role']
        }))

    async def piece_lock(self, event):
        await self.send(text_data=json.dumps({
            'type': 'piece_lock',
            'piece_id': event['piece_id'],
            'locked_by': event['locked_by'],
        }))

    async def piece_unlock(self, event):
        await self.send(text_data=json.dumps({
            'type': 'piece_unlock',
            'piece_id': event['piece_id'],
        }))

    async def player_ready(self, event):
        await self.send(text_data=json.dumps({
            'type': 'player_ready',
            'player_role': event['player_role'],
            'is_ready': event['is_ready'],
        }))

    async def both_ready(self, event):
        await self.send(text_data=json.dumps({
            'type': 'both_ready',
            'message': 'Both players are ready. Timer started!',
        }))

    @database_sync_to_async
    def reset_piece_position(self, piece_id):
        """Resets the piece's position to its initial state in the database."""
        piece = JigsawPuzzlePiece.objects.get(id=piece_id)
        piece.x_position = None  # Reset position
        piece.y_position = None
        piece.is_placed = False  # Mark as not placed
        piece.locked_by = None  # Unlock the piece
        piece.save()


    
    @database_sync_to_async
    def update_piece_position(self, piece_id, new_x, new_y, player_role):
        piece = JigsawPuzzlePiece.objects.get(id=piece_id)
        piece.x_position = new_x
        piece.y_position = new_y
        piece.is_placed = True
        piece.placed_by = player_role
        piece.locked_by = None
        piece.save()


    @database_sync_to_async
    def lock_piece(self, piece_id, player_role):
        piece = JigsawPuzzlePiece.objects.get(id=piece_id)
        if not piece.locked_by:
            piece.locked_by = player_role
            piece.save()
            return True
        return False

    @database_sync_to_async
    def unlock_piece(self, piece_id):
        piece = JigsawPuzzlePiece.objects.get(id=piece_id)
        if piece.locked_by:
            piece.locked_by = None
            piece.save()
            return True
        return False

    @database_sync_to_async
    def update_player_ready_status(self, player_role, is_ready):
        room = JigsawPuzzleRoom.objects.get(id=self.room_id)
        if player_role == 'player1':
            room.player1_ready = is_ready
        elif player_role == 'player2':
            room.player2_ready = is_ready
        room.save()

    @database_sync_to_async
    def lock_piece_position(self, piece_id, new_x, new_y):
        piece = JigsawPuzzlePiece.objects.get(id=piece_id)
        
        expected_x = piece.grid_x * self.base_grid_size
        expected_y = piece.grid_y * self.base_grid_size
        
        tolerance = 20  # 20px tolerance
        if abs(new_x - expected_x) <= tolerance and abs(new_y - expected_y) <= tolerance:
            piece.x_position = new_x
            piece.y_position = new_y
            piece.is_correct = True
            piece.is_locked = True  # Lock the piece position once correct
            piece.save()
            return True
        else:
            piece.is_correct = False
            piece.save()
            return False

    @database_sync_to_async
    def is_piece_correct(self, piece_id, base_grid_size):
        piece = JigsawPuzzlePiece.objects.get(id=piece_id)
        piece.refresh_from_db()

        # Calculate which grid cell the piece is in based on its position
        current_grid_x = round(piece.x_position / base_grid_size)
        current_grid_y = round(piece.y_position / base_grid_size)

        # The expected grid positions are already in grid coordinates
        expected_grid_x = piece.grid_x
        expected_grid_y = piece.grid_y

        print(f"🔍 Piece {piece_id} | Current grid: ({current_grid_x}, {current_grid_y}) | Expected grid: ({expected_grid_x}, {expected_grid_y})")

        # Compare the rounded grid positions
        is_correct = (current_grid_x == expected_grid_x and current_grid_y == expected_grid_y)

        if is_correct:
            piece.is_correct = True
            print(f"Piece {piece_id} is in the correct grid cell!")
        else:
            piece.is_correct = False
            print(f"Piece {piece_id} is NOT in the correct grid cell!")
        
        piece.save()
        return piece.is_correct

    async def is_puzzle_completed(self):
        room = await database_sync_to_async(JigsawPuzzleRoom.objects.get)(id=self.room_id)
        
        if room.completed:  # If already completed, don't check again
            return True

        if room.mode == "collaborative":
            # Check if all pieces are correct
            all_correct = await database_sync_to_async(
                lambda: not JigsawPuzzlePiece.objects.filter(room=room, is_correct=False).exists()
            )()
            
            if all_correct:
                room.completed = True
                room.completion_time = int((timezone.now() - room.start_time).total_seconds())
                await database_sync_to_async(room.save)()

                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'puzzle_completed',
                        'message': 'Puzzle is completed!',
                        'completion_time': room.completion_time,
                        'moves_taken': room.moves_taken
                    }
                )
                return True
            return False

        elif room.mode == "versus":
            # Check if either player has completed their pieces
            player1_done = await database_sync_to_async(
                lambda: not JigsawPuzzlePiece.objects.filter(room=room, player_assignment="player1", is_correct=False).exists()
            )()
            player2_done = await database_sync_to_async(
                lambda: not JigsawPuzzlePiece.objects.filter(room=room, player_assignment="player2", is_correct=False).exists()
            )()

            if player1_done or player2_done:
                # Determine winner
                winner = None
                if player1_done and not player2_done:
                    winner = await database_sync_to_async(lambda: room.player1)()
                elif player2_done and not player1_done:
                    winner = await database_sync_to_async(lambda: room.player2)()
                elif player1_done and player2_done:
                    # Tiebreaker: Who took fewer moves?
                    if room.player1_moves < room.player2_moves:
                        winner = await database_sync_to_async(lambda: room.player1)()
                    else:
                        winner = await database_sync_to_async(lambda: room.player2)()

                if winner:
                    room.completed = True
                    room.winner = winner
                    room.completion_time = int((timezone.now() - room.start_time).total_seconds())
                    await database_sync_to_async(room.save)()

                    await self.channel_layer.group_send(
                        self.room_group_name,
                        {
                            'type': 'puzzle_completed',
                            'message': f"{winner.username} has won the puzzle!",
                            'winner': winner.username,
                            'completion_time': room.completion_time,
                            'moves_taken': room.moves_taken
                        }
                    )
                    return True
            return False

    async def game_over(self, event):
        await self.send(text_data=json.dumps({
            'type': 'game_over',
            'message': event['message'],
            'winner': event['winner'],
            'elapsed_time': event['elapsed_time'],
            'winner_moves': event['winner_moves'],
        }))

    async def mark_puzzle_as_completed(self):
        room = await database_sync_to_async(JigsawPuzzleRoom.objects.get)(id=self.room_id)

        # Ensure start_time is set
        if not room.start_time:
            room.start_time = timezone.now()
            await database_sync_to_async(room.save)()

        elapsed_time = (timezone.now() - room.start_time).total_seconds()
        moves_taken = room.moves_taken  

        room.completed = True
        room.completion_time = int(elapsed_time)
        await database_sync_to_async(room.save)()
        logger.info(f"📡 Sending puzzle completion event: {elapsed_time} seconds, {moves_taken} moves")

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'puzzle_completed',

                'message': 'Puzzle is completed!',
                'completion_time': int(elapsed_time),
                'moves_taken': moves_taken,
            }
        )
