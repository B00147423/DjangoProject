from django.db import models
from puzzles.models import Puzzle

class PuzzleRoom(models.Model):
    room_id = models.CharField(max_length=100, unique=True)
    name = models.CharField(max_length=100) 
    puzzle = models.ForeignKey(Puzzle, on_delete=models.CASCADE)  # Room is linked to one puzzle
    state = models.JSONField(default=dict)  # Track puzzle piece positions
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Room {self.room_id} - Puzzle: {self.puzzle.title}"
