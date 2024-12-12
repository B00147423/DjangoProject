import os
import django
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack

# Set up the DJANGO_SETTINGS_MODULE environment variable
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "PuzzleRoom.PuzzleRoom.settings")

# Initialize Django
django.setup()

# Import WebSocket routing after Django setup to avoid circular imports
from jigsaw_puzzle.routing import websocket_urlpatterns as jigsaw_websocket_urlpatterns
from sliding_puzzle.routing import websocket_urlpatterns as sliding_websocket_urlpatterns

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter(
            jigsaw_websocket_urlpatterns + sliding_websocket_urlpatterns
        )
    ),
})
