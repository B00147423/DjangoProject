# jigsaw_puzzle/consumers.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import JigsawPuzzlePiece, JigsawPuzzleRoom
from asgiref.sync import async_to_sync
from django.utils import timezone
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

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        data = json.loads(text_data)
        message_type = data['type']

        if message_type == 'piece_move':
            # Handle piece movement
            piece_id = data['piece_id']
            new_x = data['new_x']
            new_y = data['new_y']
            player_role = data['player_role']
            image_url = data.get('image_url', '')


            # Validate mode
            room = await database_sync_to_async(JigsawPuzzleRoom.objects.get)(id=self.room_id)
            if room.mode == "versus" and player_role not in ["player1", "player2"]:
                return  # Ignore invalid player actions in versus mode

            # Update piece position in database
            await self.update_piece_position(piece_id, new_x, new_y, player_role)
            # Get image URL for broadcasting
            piece = await database_sync_to_async(JigsawPuzzlePiece.objects.get)(id=piece_id)
            image_url = piece.image_piece.url

            # Broadcast the move to all clients
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'piece_move',
                    'piece_id': piece_id,
                    'new_x': new_x,
                    'new_y': new_y,
                    'player_role': player_role,
                    'image_url': image_url,
                }
            )
        elif message_type == 'piece_remove':
            piece_id = data['piece_id']
            player_role = data['player_role']
            await self.reset_piece_position(piece_id)

            # Broadcast the removal to all clients
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'piece_remove',
                    'piece_id': piece_id,
                    'player_role': player_role,
                }
            )
        elif message_type == 'player_ready':
            # Handle player ready status
            player_role = data['player_role']
            is_ready = data['is_ready']
            await self.update_player_ready_status(player_role, is_ready)
            # Broadcast the ready status to all clients
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'player_ready',
                    'player_role': player_role,
                    'is_ready': is_ready,
                }
            )
            
            # Check if both players are ready
            room = await database_sync_to_async(JigsawPuzzleRoom.objects.get)(id=self.room_id)
            if room.player1_ready and room.player2_ready:
                if room.start_time is None:
                    room.start_time = timezone.now()
                    await database_sync_to_async(room.save)()

                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'both_ready',
                    }
                )
                
        elif message_type == 'piece_lock':
            # Handle piece locking
            piece_id = data['piece_id']
            player_role = data['player_role']
            if await self.lock_piece(piece_id, player_role):
                # Broadcast the lock to other clients
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'piece_lock',
                        'piece_id': piece_id,
                        'locked_by': player_role,
                    }
                )

        elif message_type == 'piece_unlock':
            # Handle piece unlocking
            piece_id = data['piece_id']
            if await self.unlock_piece(piece_id):
                # Broadcast the unlock to other clients
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'piece_unlock',
                        'piece_id': piece_id,
                    }
                )

    async def piece_move(self, event):
        # Send piece move to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'piece_move',
            'piece_id': event['piece_id'],
            'new_x': event['new_x'],
            'new_y': event['new_y'],
            'player_role': event['player_role'],
            'image_url': event['image_url'],
        }))

    async def piece_remove(self, event):
        # Send piece remove to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'piece_remove',
            'piece_id': event['piece_id'],
            'player_role': event['player_role'],
        }))


    async def piece_lock(self, event):
        # Send piece lock to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'piece_lock',
            'piece_id': event['piece_id'],
            'locked_by': event['locked_by'],
        }))

    async def piece_unlock(self, event):
        # Send piece unlock to WebSocket
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
        piece = JigsawPuzzlePiece.objects.get(id=piece_id)
        piece.x_position = None  # Reset to default
        piece.y_position = None
        piece.is_placed = False
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
        if not piece.locked_by:  # Only lock if it is not already locked
            piece.locked_by = player_role
            piece.save()
            return True
        return False

    @database_sync_to_async
    def unlock_piece(self, piece_id):
        piece = JigsawPuzzlePiece.objects.get(id=piece_id)
        if piece.locked_by:  # Only unlock if it is currently locked
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
    
    async def select_piece(self, piece_id, player_role):
        # Lock the piece for the player
        piece = await database_sync_to_async(JigsawPuzzlePiece.objects.get)(id=piece_id)
        if piece.locked_by is None:
            piece.locked_by = player_role
            await database_sync_to_async(piece.save)()
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'piece_locked',
                    'piece_id': piece_id,
                    'player_role': player_role
                }
            )

    def receive_json(self, content):
        command = content.get('command', None)
        if command == 'select_piece':
            self.select_piece(content['piece_id'], content['player_role'])
        elif command == 'move_piece':
            self.move_piece(content['piece_id'], content['new_x'], content['new_y'], content['player_role'])