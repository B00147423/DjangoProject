#C:\Users\beka\OneDrive\Desktop\Year4DjangoMajor-Project\DjangoProject\PuzzleRoom\puzzles\models.py
from django.db import models

# Create your models here.
class Puzzle(models.Model):
    title = models.CharField(max_length=100)
    name = models.CharField(max_length=100)
    image = models.ImageField(upload_to='puzzles/')
    rows = models.IntegerField(default=4)
    cols = models.IntegerField(default=4)
    created_at = models.DateTimeField(auto_now_add=True)
    difficulty = models.CharField(max_length=50, choices=[('Easy', 'Easy'), ('Medium', 'Medium'), ('Hard', 'Hard')])

from django.db import models
from puzzles.models import Puzzle
from rooms.models import PuzzleRoom

class PuzzlePiece(models.Model):
    puzzle = models.ForeignKey(Puzzle, on_delete=models.CASCADE)
    room = models.ForeignKey(PuzzleRoom, on_delete=models.CASCADE)
    image_path = models.CharField(max_length=255)  # Path to the piece's image
    original_col = models.IntegerField()  # The correct column the piece belongs in
    original_row = models.IntegerField()  # The correct row the piece belongs in
    current_col = models.IntegerField(null=True, blank=True)  # The current column of the piece
    current_row = models.IntegerField(null=True, blank=True)  # The current row of the piece
    is_correct = models.BooleanField(default=False)  # Whether the piece is placed in the correct position

    def __str__(self):
        return f"Piece {self.id} in Puzzle {self.puzzle.title} (Room: {self.room.name})"
