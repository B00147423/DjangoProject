from django.db import models

# Create your models here.
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()
from django.conf import settings

class PhysicsPuzzleRoom(models.Model):
    player1 = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    puzzle_image = models.ImageField(upload_to='puzzles/')
    created_at = models.DateTimeField(auto_now_add=True)
    name = models.CharField(max_length=100)  # ✅ Ensure this field exists

class PhysicsPuzzlePiece(models.Model):
    room = models.ForeignKey("PhysicsPuzzleRoom", on_delete=models.CASCADE)
    image_piece = models.ImageField(upload_to='puzzle_pieces/')
    initial_x = models.IntegerField()
    initial_y = models.IntegerField()
    is_placed = models.BooleanField(default=False)

    # ✅ Add default values
    correct_x = models.IntegerField(default=0)  
    correct_y = models.IntegerField(default=0)  
    is_stuck = models.BooleanField(default=False)