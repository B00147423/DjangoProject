#C:\Users\beka\OneDrive\Desktop\Year4DjangoMajor-Project\DjangoProject\PuzzleRoom\jigsaw_puzzle\urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('create_room/jigsaw/', views.create_jigsaw_room, name='create_jigsaw_room'),
    path('collaborative_room/<int:room_id>/', views.collaborative_jigsaw_room, name='collaborative_room'),
    path('waiting_room/<int:room_id>/', views.waiting_room, name='waiting_room'),
    path('join_room/<int:room_id>/', views.join_room, name='join_room'),
    path('room/<int:room_id>/', views.jigsaw_puzzle_room, name='jigsaw_puzzle_room'),
    path('check_player2_status/<int:room_id>/', views.check_player2_status, name='check_player2_status'),
    # Other URLs as needed
]