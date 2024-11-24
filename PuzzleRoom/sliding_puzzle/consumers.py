# C:\Users\beka\OneDrive\Desktop\Year4DjangoMajor-Project\DjangoProject\PuzzleRoom\sliding_puzzle\consumers.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from puzzles.models import PuzzlePiece
from sliding_puzzle.models import PuzzleRoom
import logging

logger = logging.getLogger(__name__)

class RoomConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_id = self.scope['url_route']['kwargs']['room_id']
        self.room_group_name = f'room_{self.room_id}'

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        data = json.loads(text_data)
        piece_id = data.get('piece_id')
        col_target = data.get('col_target')
        row_target = data.get('row_target')

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
        piece_id = event['piece_id']
        col_target = event['col_target']
        row_target = event['row_target']

        await self.send(text_data=json.dumps({
            'piece_id': piece_id,
            'col_target': col_target,
            'row_target': row_target,
        }))

    @database_sync_to_async
    def update_puzzle_piece(self, piece_id, col_target, row_target):
        try:
            piece = PuzzlePiece.objects.get(id=piece_id)
            piece.current_col = col_target
            piece.current_row = row_target
            piece.is_correct = (piece.current_col == piece.correct_col) and (piece.current_row == piece.correct_row)
            piece.save()
            logger.info(f"Updated PuzzlePiece {piece_id}: Col {col_target}, Row {row_target}, Correct: {piece.is_correct}")
        except PuzzlePiece.DoesNotExist:
            logger.error(f"PuzzlePiece with id {piece_id} does not exist.")

    @database_sync_to_async
    def check_puzzle_completion(self):
        room = PuzzleRoom.objects.get(room_id=self.room_id)
        all_correct = PuzzlePiece.objects.filter(room=room, is_correct=True).count() == room.puzzle.rows * room.puzzle.cols
        return all_correct

    async def move_piece(self, event):
        await self.send(text_data=json.dumps({
            'piece_id': event['piece_id'],
            'col_target': event['col_target'],
            'row_target': event['row_target'],
            'user_id': event['user_id'],
            'username': event['username'],
        }))

    async def new_participant(self, event):
        await self.send(text_data=json.dumps({
            'new_participant': event['name'],
        }))