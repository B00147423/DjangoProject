# jigsaw_puzzle/models.py

from django.conf import settings
from django.db import models
from django.contrib.auth import get_user_model
import random
import string
from django.utils import timezone
import os
User = get_user_model()
import logging
logger = logging.getLogger(__name__)

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

    start_time = models.DateTimeField(null=True, blank=True)
    total_duration = models.IntegerField(default=2700)

    completed = models.BooleanField(default=False)
    moves_taken = models.IntegerField(default=0)
    completion_time = models.IntegerField(default=0)
    winner = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="won_games")
    player1_moves = models.IntegerField(default=0)
    player2_moves = models.IntegerField(default=0)
    
    def get_elapsed_time(self):
        """Calculate the elapsed time even if the game is still running."""
        if self.completed:
            return self.completion_time
        if self.start_time:
            return int((timezone.now() - self.start_time).total_seconds())
        return 0

    def check_puzzle_completion(self):
        pieces = JigsawPuzzlePiece.objects.filter(room=self)
        all_correct = all(piece.is_correct for piece in pieces)
        logger.info(f"Checking puzzle completion: all_correct={all_correct}, completed={self.completed}")
        if all_correct and not self.completed:
            self.mark_completed()

    def mark_completed(self):
        logger.info(f"Marking room {self.id} as completed")
        self.completed = True
        self.save()

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
    
    def cleanup(self):
        # Delete all puzzle pieces
        pieces = JigsawPuzzlePiece.objects.filter(room=self)
        for piece in pieces:
            if piece.image_piece and os.path.exists(piece.image_piece.path):
                os.remove(piece.image_piece.path)
            piece.delete()
        
        if self.puzzle_image and os.path.exists(self.puzzle_image.path):
            os.remove(self.puzzle_image.path)
        
        self.delete()
    



class JigsawPuzzlePiece(models.Model):
    room = models.ForeignKey(JigsawPuzzleRoom, on_delete=models.CASCADE)
    image_piece = models.ImageField(max_length=500, blank=True, null=True)
    x_position = models.IntegerField(null=True, blank=True)
    y_position = models.IntegerField(null=True, blank=True)
    initial_x = models.IntegerField(null=False, blank=False, default=0)
    initial_y = models.IntegerField(null=False, blank=False, default=0)
    is_correct = models.BooleanField(default=False)
    is_placed = models.BooleanField(default=False)
    grid_x = models.IntegerField(null=False, blank=False, default=0)
    grid_y = models.IntegerField(null=False, blank=False, default=0)
    placed_by = models.CharField(max_length=50, null=True, blank=True)  
    player_assignment = models.CharField(max_length=15, null=True) 
    locked_by = models.CharField(max_length=100, null=True, blank=True)
    edges = models.JSONField(default=dict, null=True, blank=True)
    player_assignment = models.CharField(max_length=15, choices=[('player1', 'Player 1'), ('player2', 'Player 2')], null=True)
    neighbors = models.ManyToManyField("self", symmetrical=True)  
    def __str__(self):
        return f"Piece in {self.room.name}"

    def set_neighbors(self):
        """Find and set this piece's neighbors"""
        neighbors = JigsawPuzzlePiece.objects.filter(
            room=self.room,
            grid_x__in=[self.grid_x - 1, self.grid_x + 1],
            grid_y__in=[self.grid_y - 1, self.grid_y + 1]
        )
        self.neighbors.set(neighbors)    
        
    def image_url(self):
        """Generate full URL for puzzle piece image"""
        return f"{settings.MEDIA_URL}{self.image_piece}"
    
    def check_and_update_position(self):
        """Check if this piece is correctly placed and update its status"""
        if self.x_position == self.grid_x and self.y_position == self.grid_y:
            self.is_correct = True
        else:
            self.is_correct = False
        self.save()


class ChatMessage(models.Model):
    room = models.ForeignKey('JigsawPuzzleRoom', on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username}: {self.message[:50]}"
    

class Leaderboard(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    room = models.ForeignKey(JigsawPuzzleRoom, on_delete=models.CASCADE)
    completion_time = models.IntegerField()
    moves_taken = models.IntegerField()
    date = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['completion_time']

    def __str__(self):
        return f"{self.user.username} - {self.completion_time} sec"
