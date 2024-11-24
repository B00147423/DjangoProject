
# C:\Users\beka\OneDrive\Desktop\Year4DjangoMajor-Project\DjangoProject\PuzzleRoom\puzzles\urls.py
from django.conf import settings
from django.urls import path
from .views import room_selection
from jigsaw_puzzle.views import create_jigsaw_room
from sliding_puzzle.views import create_room
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
urlpatterns = [
    path('select-room/', room_selection, name='room_selection'),
    path('create-jigsaw-room/', create_jigsaw_room, name='create_jigsaw_room'),
    path('create-room/', create_room, name='create_room'),
]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)