#C:\Users\beka\OneDrive\Desktop\Year4DjangoMajor-Project\DjangoProject\PuzzleRoom\sliding_puzzle\urls.py
from django.urls import path
from . import views

app_name = 'sliding_puzzle'

urlpatterns = [
    path('create/', views.create_room, name='create_room'),
    path('room/<str:room_id>/', views.room_detail, name='room_detail'),
    path('save-puzzle-state/<str:room_id>/', views.save_puzzle_state, name='save_puzzle_state'),
    path('invite/<uuid:invite_token>/', views.join_room_via_invite, name='join_room_via_invite'),
    path('generate-invite-link/<str:room_id>/', views.generate_invite_link, name='generate_invite_link'),
]