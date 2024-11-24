#C:\Users\beka\OneDrive\Desktop\Year4DjangoMajor-Project\DjangoProject\PuzzleRoom\sliding_puzzle\models.py
from django.db import models
import uuid
from django.contrib.auth import get_user_model

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

    