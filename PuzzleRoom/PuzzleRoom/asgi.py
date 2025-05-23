import os
import django
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "PuzzleRoom.settings")

django.setup()

from jigsaw_puzzle.routing import websocket_urlpatterns as jigsaw_websocket_urlpatterns
from sliding_puzzle.routing import websocket_urlpatterns as sliding_websocket_urlpatterns
from physics_puzzle.routing import websocket_urlpatterns as physics_websocket_urlpatterns  # ✅ Add this

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter(
            jigsaw_websocket_urlpatterns + sliding_websocket_urlpatterns + physics_websocket_urlpatterns 
        )
    ),
})
