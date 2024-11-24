# C:\Users\beka\OneDrive\Desktop\Year4DjangoMajor-Project\DjangoProject\PuzzleRoom\sliding_puzzle\routing.py

from django.urls import path
from . import consumers  # Import the consumer that will handle the WebSocket

# Define WebSocket routes
websocket_urlpatterns = [
    path('ws/sliding_puzzle/<str:room_id>/', consumers.RoomConsumer.as_asgi()),
]
