# jigsaw_puzzle/consumers.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import JigsawPuzzlePiece, JigsawPuzzleRoom

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

            # Update piece position in database
            try:
                piece = await database_sync_to_async(JigsawPuzzlePiece.objects.get)(id=piece_id)
                piece.x_position = new_x
                piece.y_position = new_y
                piece.is_placed = True
                piece.placed_by = player_role
                await database_sync_to_async(piece.save)()

                # Broadcast the move to all clients
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'piece_move',
                        'piece_id': piece_id,
                        'new_x': new_x,
                        'new_y': new_y,
                        'player_role': player_role,
                        'image_url': image_url
                    }
                )
            except JigsawPuzzlePiece.DoesNotExist:
                pass

        elif message_type == 'piece_remove':
            # Handle piece removal
            piece_id = data['piece_id']
            player_role = data['player_role']

            # Update database to remove piece placement
            try:
                piece = await database_sync_to_async(JigsawPuzzlePiece.objects.get)(id=piece_id)
                piece.is_placed = False
                piece.x_position = None
                piece.y_position = None
                piece.placed_by = None
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
            except JigsawPuzzlePiece.DoesNotExist:
                pass
    async def piece_move(self, event):
        # Send piece move to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'piece_move',
            'piece_id': event['piece_id'],
            'new_x': event['new_x'],
            'new_y': event['new_y'],
            'player_role': event['player_role'],
            'image_url': event['image_url']
        }))

    async def piece_remove(self, event):
        # Send piece removal to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'piece_remove',
            'piece_id': event['piece_id'],
            'player_role': event['player_role']
        }))


    @database_sync_to_async
    def update_piece_position(self, piece_id, new_x, new_y, player_role):
        piece = JigsawPuzzlePiece.objects.get(id=piece_id)
        piece.x_position = new_x
        piece.y_position = new_y
        piece.is_placed = True
        piece.placed_by = player_role
        piece.save()

    @database_sync_to_async
    def get_all_pieces(self):
        room = JigsawPuzzleRoom.objects.get(id=self.room_id)
        pieces = JigsawPuzzlePiece.objects.filter(room=room)
        return [
            {
                'id': piece.id,
                'x': piece.x_position,
                'y': piece.y_position,
                'image_url': piece.image_url,
                'is_placed': piece.is_placed,
                'placed_by': piece.placed_by
            } for piece in pieces
        ]
