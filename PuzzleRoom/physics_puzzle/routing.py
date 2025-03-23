from django.urls import re_path
from physics_puzzle.consumers import PhysicsPuzzleConsumer

websocket_urlpatterns = [
    re_path(r'ws/physics/(?P<room_id>\d+)/$', PhysicsPuzzleConsumer.as_asgi()),
]