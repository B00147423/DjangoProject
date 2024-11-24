# C:\Users\beka\OneDrive\Desktop\Year4DjangoMajor-Project\DjangoProject\PuzzleRoom\puzzles\views.py
from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def room_selection(request):
    return render(request, 'puzzles/room_selection.html')

@login_required
def create_jigsaw_room(request):
    return render(request, 'jigsaw_puzzle/create_room.html') 

def create_room(request):
    return render(request, 'sliding_puzzle/create_room.html')
