#C:\Users\beka\OneDrive\Desktop\Year4DjangoMajor-Project\DjangoProject\PuzzleRoom\jigsaw_puzzle\routing.py
from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/puzzle/(?P<room_id>\d+)/$', consumers.PuzzleConsumer.as_asgi()),
]
