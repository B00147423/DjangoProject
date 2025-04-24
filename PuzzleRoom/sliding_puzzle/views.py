# C:\Users\beka\OneDrive\Desktop\Year4DjangoMajor-Project\DjangoProject\PuzzleRoom\sliding_puzzle\tests.py
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from .models import PuzzleRoom
from django.contrib.auth.decorators import login_required
import uuid
from django.conf import settings
import json
from puzzles.models import PuzzlePiece
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from .models import PuzzleRoom
from puzzles.models import Puzzle, PuzzlePiece
import uuid
import random
from django.core.files.storage import default_storage
from PIL import Image
import os
from datetime import datetime
import cloudinary.uploader
from django.conf import settings
from django.core.files.storage import FileSystemStorage

@login_required
def room_full(request):
    return render(request, 'sliding_puyzzle/room_full.html')
from io import BytesIO

@login_required
def create_room(request):
    if request.method == "POST":
        room_name = request.POST.get('roomName')
        difficulty = request.POST.get('difficulty')

        if 'puzzleImage' not in request.FILES:
            return JsonResponse({'error': 'No image uploaded'}, status=400)

        uploaded_image = request.FILES['puzzleImage']

        fs = FileSystemStorage()
        filename = fs.save(uploaded_image.name, uploaded_image)
        image_path = fs.path(filename)

        # Set grid size
        grid_sizes = {'easy': 3, 'medium': 4, 'hard': 5}
        grid_size = grid_sizes.get(difficulty.lower(), 4)
        pieces = [i for i in range(1, grid_size * grid_size)] + ['empty']
        random.shuffle(pieces)

        puzzle = Puzzle.objects.create(
            title=f"Sliding Puzzle {str(uuid.uuid4())[:8]}",
            rows=grid_size,
            cols=grid_size,
            difficulty=difficulty,
        )

        initial_state = {
            'pieces': pieces,
            'grid_size': grid_size,
            'move_count': 0,
            'start_time': int(datetime.now().timestamp() * 1000),
            'is_completed': False,
            'best_time': None,
            'best_moves': None,
            'games_completed': 0
        }

        new_room = PuzzleRoom.objects.create(
            room_id=str(uuid.uuid4()),
            name=room_name,
            puzzle=puzzle,
            state=initial_state
        )

        image = Image.open(image_path)
        split_image_and_create_pieces(new_room, image, puzzle)

        return redirect('sliding_puzzle:room_detail', room_id=new_room.room_id)

def split_image_and_create_pieces(room, image, puzzle):
    grid_size = puzzle.rows
    img_width, img_height = image.size
    tile_width = img_width // grid_size
    tile_height = img_height // grid_size

    # Create folder for storing tiles
    # Save tiles to match frontend expectation: /media/puzzles/<room_id>/tile_0_0.png
    folder_path = os.path.join(settings.MEDIA_ROOT, 'puzzles', room.room_id)
    os.makedirs(folder_path, exist_ok=True)


    for row in range(grid_size):
        for col in range(grid_size):
            if row == grid_size - 1 and col == grid_size - 1:
                continue  # Skip the empty space

            left = col * tile_width
            upper = row * tile_height
            right = left + tile_width
            lower = upper + tile_height

            tile = image.crop((left, upper, right, lower))

            # Save the tile locally
            filename = f"tile_{row}_{col}.png"
            file_path = os.path.join(folder_path, filename)
            tile.save(file_path)

            # Relative path to save in model (for serving later)
            relative_path = os.path.join('puzzles', 'pieces', room.room_id, filename)

            PuzzlePiece.objects.create(
                puzzle=puzzle,
                room=room,
                number=row * grid_size + col + 1,
                current_row=row,
                current_col=col,
                is_correct=False,
                image=relative_path
            )


@login_required
def room_detail(request, room_id):
    room = get_object_or_404(PuzzleRoom, room_id=room_id)
    puzzle_pieces = PuzzlePiece.objects.filter(room=room)

    puzzle_state = {
        'pieces': room.state.get('pieces', []),
        'grid_size': room.puzzle.rows,
        'move_count': room.state.get('move_count', 0),
        'best_time': room.state.get('best_time'),
        'best_moves': room.state.get('best_moves'),
        'games_completed': room.state.get('games_completed', 0),
        'is_completed': room.state.get('is_completed', False),
        'start_time': room.state.get('start_time')
    }

    context = {
        'room': room,
        'puzzle_pieces': puzzle_pieces,
        'puzzle_state': json.dumps(puzzle_state),
        'MEDIA_URL': settings.MEDIA_URL,
    }

    return render(request, 'sliding_puzzle/room_detail.html', context)

def save_puzzle_state(request, room_id):
    if request.method == 'POST':
        room = get_object_or_404(PuzzleRoom, room_id=room_id)
        data = json.loads(request.body)
        puzzle_state = data.get('puzzleState', [])
        grid_size = room.puzzle.rows

        # Update piece positions
        for index, tile_number in enumerate(puzzle_state):
            if tile_number != 'empty':
                try:
                    piece = PuzzlePiece.objects.get(puzzle=room.puzzle, number=tile_number)
                    piece.current_col = index % grid_size
                    piece.current_row = index // grid_size
                    piece.is_correct = (piece.current_col == (tile_number - 1) % grid_size and 
                                      piece.current_row == (tile_number - 1) // grid_size)
                    piece.save()
                except PuzzlePiece.DoesNotExist:
                    return JsonResponse({'error': f"PuzzlePiece {tile_number} not found"}, status=400)

        # Update room state with all game data
        current_state = room.state
        current_state.update({
            'pieces': puzzle_state,
            'grid_size': grid_size,
            'move_count': data.get('moveCount', 0),
            'current_time': data.get('current_time', 0),
            'is_completed': data.get('is_completed', False),
            'start_time': data.get('start_time')
        })

        # Update best scores only if they're better than current ones
        if data.get('best_time') is not None:
            if current_state.get('best_time') is None or data['best_time'] < current_state['best_time']:
                current_state['best_time'] = data['best_time']

        if data.get('best_moves') is not None:
            if current_state.get('best_moves') is None or data['best_moves'] < current_state['best_moves']:
                current_state['best_moves'] = data['best_moves']

        # Update games completed
        current_state['games_completed'] = data.get('games_completed', current_state.get('games_completed', 0))

        room.state = current_state
        room.save()

        return JsonResponse({'status': 'success'})

    return JsonResponse({'error': 'Invalid request'}, status=400)

@login_required
def join_room(request, room_id):
    room = get_object_or_404(PuzzleRoom, room_id=room_id)

    if room.player1 is None:
        room.player1 = request.user
    elif room.player2 is None:
        room.player2 = request.user
    else:
        return redirect('room_full')  # If both players are already assigned, room is full

    room.save()
    return redirect('room_detail', room_id=room_id)

@require_http_methods(["GET", "POST"])
def join_room_via_invite(request, invite_token):
    room = get_object_or_404(PuzzleRoom, invite_token=invite_token)

    # Check if invite link has already been used
    if room.invite_used:
        messages.error(request, "This invite link has already been used.")
        return redirect('room_full')

    if request.user.is_authenticated:
        if room.player1 is None:
            room.player1 = request.user
            room.invite_used = True
        elif room.player2 is None:
            room.player2 = request.user
            room.invite_used = True
        else:
            messages.error(request, "The room is full.")
            return redirect('room_full')

        room.save()

        messages.success(request, f'You have joined the room: {room.name}')
        notify_new_participant(room, request.user.username)
    else:
        # Handle guest login or other cases here
        pass

    return redirect('room_detail', room_id=room.room_id)

def notify_new_participant(room, participant_name):
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f'room_{room.room_id}',
        {
            'type': 'new_participant',
            'name': participant_name,
        }
    )

@login_required
def generate_invite_link(request, room_id):
    room = get_object_or_404(PuzzleRoom, room_id=room_id)

    # Generate the invite link using the invite_token
    invite_link = f"{request.build_absolute_uri('/')}rooms/invite/{room.invite_token}/"

    return JsonResponse({'invite_link': invite_link, 'status': 'success'})