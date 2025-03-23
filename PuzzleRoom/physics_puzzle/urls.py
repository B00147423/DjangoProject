from django.urls import path
from .views import physics_puzzle_room, create_physics_room

urlpatterns = [
    path('physics-room/<int:room_id>/', physics_puzzle_room, name='physics_puzzle_room'),
    path('create/', create_physics_room, name='create_physics_room'),  # ✅ This is the correct URL name
]