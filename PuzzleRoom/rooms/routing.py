# rooms/routing.py

from django.urls import path
from . import consumers  # Import the consumer that will handle the WebSocket

# Define WebSocket routes
websocket_urlpatterns = [
    path('ws/room/<str:room_name>/', consumers.RoomConsumer.as_asgi()),  # Dynamic room_name in the URL
]
