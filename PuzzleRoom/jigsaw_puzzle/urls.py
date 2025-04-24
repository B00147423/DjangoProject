from django.urls import path
from . import views

app_name = 'jigsaw_puzzle'
urlpatterns = [
    path('create_room/jigsaw/', views.create_jigsaw_room, name='create_jigsaw_room'),
    path('collaborative_room/<int:room_id>/', views.collaborative_jigsaw_room, name='collaborative_room'),
    path('waiting-room/<int:room_id>/', views.waiting_room, name='waiting_room'),
    path('join_room/', views.join_room, name='join_room'),
    path('room/<int:room_id>/', views.jigsaw_puzzle_room, name='jigsaw_puzzle_room'),
    path('check_player2_status/<int:room_id>/', views.check_player2_status, name='check_player2_status'),
    path('toggle_ready_status/<int:room_id>/', views.toggle_ready_status, name='toggle_ready_status'),
    path('check_ready_status/<int:room_id>/', views.check_ready_status, name='check_ready_status'),
    path('remove_piece/<int:piece_id>/', views.remove_piece, name='remove_piece'),
    path('get_pieces/', views.get_pieces, name='get_pieces'),
    path('update_piece_position/', views.update_piece_position, name='update_piece_position'),
    path('get_remaining_time/<int:room_id>/', views.get_remaining_time, name='get_remaining_time'),
    path('completed_puzzles/', views.completed_puzzles, name='completed_puzzles'), 
    path('leaderboard/', views.leaderboard, name='leaderboard'),
]

