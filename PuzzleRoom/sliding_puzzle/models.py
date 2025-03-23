#C:\Users\beka\OneDrive\Desktop\Year4DjangoMajor-Project\DjangoProject\PuzzleRoom\sliding_puzzle\models.py
from django.db import models
import uuid
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator

User = get_user_model()

class PuzzleRoom(models.Model):
    room_id = models.CharField(max_length=100, unique=True)
    name = models.CharField(max_length=100) 
    puzzle = models.ForeignKey('puzzles.Puzzle', on_delete=models.CASCADE)  # Use string reference
    state = models.JSONField(default=dict)  # Track puzzle piece positions
    created_at = models.DateTimeField(auto_now_add=True)
    invite_token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    invite_used = models.BooleanField(default=False)
    
    # Replace RoomParticipant model with player1 and player2 fields
    player1 = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sliding_player1_rooms', null=True, blank=True)
    player2 = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='sliding_player2_rooms')

    # Game statistics
    best_time = models.IntegerField(null=True, blank=True, validators=[MinValueValidator(0)])  # Best time in seconds
    best_moves = models.IntegerField(null=True, blank=True, validators=[MinValueValidator(0)])
    games_completed = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    total_moves_made = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    current_move_count = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    last_played = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.room_id})"

    class Meta:
        ordering = ['-last_played']

class GameHistory(models.Model):
    room = models.ForeignKey(PuzzleRoom, on_delete=models.CASCADE, related_name='game_history')
    player = models.ForeignKey(User, on_delete=models.CASCADE)
    completed_at = models.DateTimeField(auto_now_add=True)
    moves_taken = models.IntegerField(validators=[MinValueValidator(0)])
    time_taken = models.IntegerField(validators=[MinValueValidator(0)])  # Time in seconds
    was_best_time = models.BooleanField(default=False)
    was_best_moves = models.BooleanField(default=False)

    class Meta:
        ordering = ['-completed_at']
        verbose_name_plural = "Game histories"

    def __str__(self):
        return f"{self.player.username}'s game - {self.moves_taken} moves in {self.time_taken}s"

    def save(self, *args, **kwargs):
        # Check if this is a new best score
        if not self.pk:  # Only on creation
            if not self.room.best_time or self.time_taken < self.room.best_time:
                self.was_best_time = True
                self.room.best_time = self.time_taken
                self.room.save(update_fields=['best_time'])
            
            if not self.room.best_moves or self.moves_taken < self.room.best_moves:
                self.was_best_moves = True
                self.room.best_moves = self.moves_taken
                self.room.save(update_fields=['best_moves'])

        super().save(*args, **kwargs)

    