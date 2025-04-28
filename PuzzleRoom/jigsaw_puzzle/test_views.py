# test_views.py (Django TestCase)
from django.test import TestCase
from sliding_puzzle.models import PuzzleRoom, PuzzlePiece
import json

class PuzzleStateTests(TestCase):
    def setUp(self):
        self.room = PuzzleRoom.objects.create(
            room_id="test_room",
            name="Test Room",
            state={"pieces": [1, 2, "empty"], "grid_size": 2}
        )
        PuzzlePiece.objects.create(
            puzzle=self.room.puzzle,
            number=1,
            current_row=0,
            current_col=0
        )

    def test_save_state(self):
        data = {
            "puzzleState": [2, 1, "empty"],
            "moveCount": 1,
            "is_completed": False
        }
        response = self.client.post(
            f"/rooms/{self.room.room_id}/save_state",
            data=json.dumps(data),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 200)
        updated_piece = PuzzlePiece.objects.get(number=1)
        self.assertEqual(updated_piece.current_col, 1) 