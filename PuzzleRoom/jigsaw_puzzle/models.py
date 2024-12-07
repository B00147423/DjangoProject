# jigsaw_puzzle/models.py

from django.db import models
from django.contrib.auth import get_user_model
import random
import string
from django.utils import timezone
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
    room_code = models.CharField(max_length=8, unique=True, blank=True, null=True)
    player1_ready = models.BooleanField(default=False)
    player2_ready = models.BooleanField(default=False)
        # Add fields for the timer
    start_time = models.DateTimeField(null=True, blank=True)
    total_duration = models.IntegerField(default=600)  # e.g. 300 seconds = 5 minutes

    def save(self, *args, **kwargs):
        if not self.room_code:
            self.room_code = self.generate_unique_code()
        super().save(*args, **kwargs)

    def generate_unique_code(self):
        while True:
            code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
            if not JigsawPuzzleRoom.objects.filter(room_code=code).exists():
                return code
            
    def get_remaining_time(self):
        """Return the remaining time in seconds."""
        if self.start_time:
            elapsed = (timezone.now() - self.start_time).total_seconds()
            remaining = self.total_duration - elapsed
            return max(int(remaining), 0)
        else:
            # If start_time is not set, no countdown has started yet
            return self.total_dura
    def __str__(self):
        return f"Jigsaw Puzzle {self.name} - {self.mode}"

class JigsawPuzzlePiece(models.Model):
    room = models.ForeignKey(JigsawPuzzleRoom, on_delete=models.CASCADE)
    image_piece = models.ImageField(upload_to='jigsaw_pieces/')
    x_position = models.IntegerField(null=True, blank=True)
    y_position = models.IntegerField(null=True, blank=True)
    initial_x = models.IntegerField(null=True, blank=True)
    initial_y = models.IntegerField(null=True, blank=True)
    is_correct = models.BooleanField(default=False)
    is_placed = models.BooleanField(default=False)
    placed_by = models.CharField(max_length=50, null=True, blank=True)  # Increased max_length
    player_assignment = models.CharField(max_length=15, null=True)  # Increased max_length
    locked_by = models.CharField(max_length=100, null=True, blank=True)

    def __str__(self):
        return f"Piece in {self.room.name}"

    @property
    def image_url(self):
        if self.image_piece:
            return self.image_piece.url
        else:
            return ''

