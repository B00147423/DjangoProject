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

@login_required
def room_full(request):
    return render(request, 'sliding_puyzzle/room_full.html')

@login_required
def create_room(request):
    if request.method == "POST":
        room_name = request.POST.get('roomName')
        difficulty = request.POST.get('difficulty')

        # Ensure image is uploaded
        if 'puzzleImage' not in request.FILES:
            return JsonResponse({'error': 'No image uploaded'}, status=400)

        uploaded_image = request.FILES['puzzleImage']

        # Save the uploaded image
        image_path = default_storage.save(f'puzzles/{uploaded_image.name}', uploaded_image)

        # Room creation logic
        room_id = str(uuid.uuid4())
        pieces = [i for i in range(1, 16)] + ['empty']
        random.shuffle(pieces)  # Shuffle pieces for puzzle

        puzzle = Puzzle.objects.create(
            title=f"Sliding Puzzle {str(uuid.uuid4())[:8]}",
            rows=4,
            cols=4,
            difficulty=difficulty,
        )

        new_room = PuzzleRoom.objects.create(
            room_id=room_id,
            name=room_name,
            puzzle=puzzle,
            state={'pieces': pieces},
        )

        # Split the uploaded image into tiles
        split_image_and_create_pieces(new_room, image_path, puzzle)

        # Generate invite link
        invite_link = f"{request.build_absolute_uri('/')}sliding_puzzle/invite/{new_room.invite_token}/"
        return JsonResponse({'room_id': room_id, 'invite_link': invite_link, 'status': 'success'})

    return render(request, 'sliding_puzzle/create_room.html')

def split_image_and_create_pieces(room, image_path, puzzle):
    directory_path = os.path.join(settings.MEDIA_ROOT, f'puzzles/{room.room_id}')
    if not os.path.exists(directory_path):
        os.makedirs(directory_path)

    # Open the uploaded image
    image = Image.open(os.path.join(settings.MEDIA_ROOT, image_path))

    img_width, img_height = image.size
    tile_width = img_width // 4
    tile_height = img_height // 4

    for row in range(4):
        for col in range(4):
            if row == 3 and col == 3:
                continue  # Skip last tile for empty space

            left = col * tile_width
            upper = row * tile_height
            right = left + tile_width
            lower = upper + tile_height

            tile = image.crop((left, upper, right, lower))

            tile_path = f'puzzles/{room.room_id}/tile_{row}_{col}.png'
            tile.save(os.path.join(settings.MEDIA_ROOT, tile_path))

            PuzzlePiece.objects.create(
                puzzle=puzzle,
                room=room,
                number=row * 4 + col + 1,
                current_row=row,
                current_col=col,
                is_correct=False,
            )

@login_required
def room_detail(request, room_id):
    room = get_object_or_404(PuzzleRoom, room_id=room_id)
    puzzle_pieces = PuzzlePiece.objects.filter(room=room)

    # Get the saved state from the room (if exists)
    saved_state = room.state.get('pieces')

    context = {
        'room': room,
        'puzzle_pieces': puzzle_pieces,
        'puzzle_state': json.dumps(saved_state),
        'MEDIA_URL': settings.MEDIA_URL,
    }

    return render(request, 'sliding_puzzle/room_detail.html', context)

def save_puzzle_state(request, room_id):
    if request.method == 'POST':
        room = get_object_or_404(PuzzleRoom, room_id=room_id)
        data = json.loads(request.body)
        puzzle_state = data.get('puzzleState', [])  # Safely get puzzleState

        for index, tile_number in enumerate(puzzle_state):
            if tile_number != 'empty':  # Ensure we're not processing the empty tile
                try:
                    piece = PuzzlePiece.objects.get(puzzle=room.puzzle, number=tile_number)
                    piece.current_col = index % 4
                    piece.current_row = index // 4
                    piece.is_correct = (piece.current_col == index % 4 and piece.current_row == index // 4)
                    piece.save()
                except PuzzlePiece.DoesNotExist:
                    return JsonResponse({'error': f"PuzzlePiece {tile_number} not found"}, status=400)

        room.state['pieces'] = puzzle_state
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