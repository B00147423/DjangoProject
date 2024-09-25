# puzzle/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('save-puzzle-state/<str:room_id>/', views.save_puzzle_state, name='save_puzzle_state'),  # URL to save the puzzle state
]