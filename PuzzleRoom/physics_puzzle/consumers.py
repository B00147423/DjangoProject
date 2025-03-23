import json
from channels.generic.websocket import AsyncWebsocketConsumer

class PhysicsPuzzleConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_id = self.scope['url_route']['kwargs']['room_id']
        self.room_group_name = f'physics_puzzle_{self.room_id}'
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

    async def receive(self, text_data):
        data = json.loads(text_data)
        if data['type'] == 'piece_move':
            await self.channel_layer.group_send(self.room_group_name, {
                'type': 'piece_update',
                'piece_id': data['piece_id'],
                'new_x': data['new_x'],
                'new_y': data['new_y']
            })

    async def piece_update(self, event):
        await self.send(text_data=json.dumps(event))
