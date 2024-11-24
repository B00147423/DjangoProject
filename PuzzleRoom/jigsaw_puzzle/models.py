# jigsaw_puzzle/models.py

from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class JigsawPuzzleRoom(models.Model):
    name = models.CharField(max_length=255)
    puzzle_image = models.ImageField(upload_to='jigsaw_puzzles/')
    difficulty = models.CharField(
        max_length=10,
        choices=[('easy', 'Easy'), ('medium', 'Medium'), ('hard', 'Hard')]
    )
    created_at = models.DateTimeField(auto_now_add=True)
    mode = models.CharField(
        max_length=15,
        choices=[('versus', 'Versus'), ('collaborative', 'Collaborative')],
        default='collaborative'
    )
    player1 = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='player1_rooms', null=True, blank=True
    )
    player2 = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name='player2_rooms'
    )

    def __str__(self):
        return f"Jigsaw Puzzle {self.name} - {self.mode}"

class JigsawPuzzlePiece(models.Model):
    room = models.ForeignKey(JigsawPuzzleRoom, on_delete=models.CASCADE)
    image_piece = models.ImageField(upload_to='jigsaw_pieces/')
    x_position = models.IntegerField(null=True, blank=True)
    y_position = models.IntegerField(null=True, blank=True)
    is_correct = models.BooleanField(default=False)
    is_placed = models.BooleanField(default=False)
    placed_by = models.CharField(max_length=10, null=True, blank=True)
    player_assignment = models.CharField(max_length=10, null=True)
    locked_by = models.CharField(max_length=100, null=True, blank=True)
    def __str__(self):
        return f"Piece in {self.room.name}"

    @property
    def image_url(self):
        if self.image_piece:
            return self.image_piece.url
        else:
            return ''
