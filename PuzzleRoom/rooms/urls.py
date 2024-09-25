# rooms/urls.py

from django.urls import path
from . import views

urlpatterns = [
    path('create-room/', views.create_room, name='create_room'),  # URL for creating a room
    path('<str:room_id>/', views.room_detail, name='room_detail'),  # URL for individual rooms
]
