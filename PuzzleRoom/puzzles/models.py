# C:\Users\beka\OneDrive\Desktop\Year4DjangoMajor-Project\DjangoProject\PuzzleRoom\puzzles\models.py
from django.db import models
from sliding_puzzle.models import PuzzleRoom
from django.contrib.auth import get_user_model

User = get_user_model()

class Puzzle(models.Model):
    title = models.CharField(max_length=100)
    rows = models.IntegerField(default=4)
    cols = models.IntegerField(default=4)
    created_at = models.DateTimeField(auto_now_add=True)
    difficulty = models.CharField(max_length=50, choices=[('Easy', 'Easy'), ('Medium', 'Medium'), ('Hard', 'Hard')])

class PuzzlePiece(models.Model):
    puzzle = models.ForeignKey(Puzzle, on_delete=models.CASCADE)
    room = models.ForeignKey(PuzzleRoom, on_delete=models.CASCADE)
    number = models.IntegerField() 
    current_col = models.IntegerField()
    current_row = models.IntegerField()
    is_correct = models.BooleanField(default=False)
    image = models.ImageField(upload_to='puzzles/pieces/', null=True, blank=True)  # ✅ Add this line

    def __str__(self):
        return f"Tile {self.number} in Room {self.room.name} (Correct: {self.is_correct})"
