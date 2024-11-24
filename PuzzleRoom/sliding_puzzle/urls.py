#C:\Users\beka\OneDrive\Desktop\Year4DjangoMajor-Project\DjangoProject\PuzzleRoom\sliding_puzzle\urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('create-room/', views.create_room, name='create_room'),
    path('room_full/', views.room_full, name='room_full'),
    path('<str:room_id>/', views.room_detail, name='room_detail'),  # This will match the /sliding_puzzle/<room_id>
    path('invite/<uuid:invite_token>/', views.join_room_via_invite, name='join_room_via_invite'),
    path('sliding_puzzle/<uuid:room_id>/join/<uuid:invite_token>/', views.join_room_via_invite, name='join_room_via_invite'),
    path('generate-invite-link/<str:room_id>/', views.generate_invite_link, name='generate_invite_link'),
    path('save-puzzle-state/<str:room_id>/', views.save_puzzle_state, name='save_puzzle_state'),
]