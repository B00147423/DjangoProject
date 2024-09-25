# rooms/consumers.py

import json
from channels.generic.websocket import AsyncWebsocketConsumer

class RoomConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f'room_{self.room_name}'

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
        piece_id = data['piece_id']
        col_target = data['col_target']
        row_target = data['row_target']

        # Broadcast the movement to all players in the room
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'puzzle_move',
                'piece_id': piece_id,
                'col_target': col_target,
                'row_target': row_target,
            }
        )

    async def puzzle_move(self, event):
        # Receive message from room group
        piece_id = event['piece_id']
        col_target = event['col_target']
        row_target = event['row_target']

        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'piece_id': piece_id,
            'col_target': col_target,
            'row_target': row_target
        }))
