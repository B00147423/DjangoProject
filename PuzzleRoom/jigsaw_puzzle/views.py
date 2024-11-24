#C:\Users\beka\OneDrive\Desktop\Year4DjangoMajor-Project\DjangoProject\PuzzleRoom\jigsaw_puzzle\views.py
from asyncio.log import logger
import random
from django.shortcuts import get_object_or_404, render, redirect
from .models import JigsawPuzzleRoom, JigsawPuzzlePiece
from .forms import JigsawPuzzleRoomForm
from PIL import Image
import os
from django.http import HttpResponse, JsonResponse
from django.core.files import File
from django.contrib.auth.models import User
import json
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model 
# jigsaw_puzzle/views.py
from django.shortcuts import render, redirect
from django.urls import reverse
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
# Get the custom User model
User = get_user_model()


@login_required
def collaborative_jigsaw_room(request, room_id):
    room = get_object_or_404(JigsawPuzzleRoom, id=room_id)
    pieces = JigsawPuzzlePiece.objects.filter(room=room)

    # Determine if the current user is Player 1 or Player 2
    player_role = 'player1' if request.user == room.player1 else 'player2'

    pieces_data = [
        {
            'image_url': piece.image_piece.url,  # This should be the image URL for the piece
            'x': piece.x_position or 0,         # Default to 0 if not set
            'y': piece.y_position or 0,         # Default to 0 if not set
            'id': piece.id
        } for piece in pieces
    ]

    # Get grid size based on difficulty
    grid_size = {
        'easy': 4,
        'medium': 6,
        'hard': 8
    }.get(room.difficulty, 4)
    cell_size = 400 // grid_size
    container_size = 400  # Adjust based on total puzzle size

    # Render the collaborative room template
    return render(request, 'jigsaw_puzzle/collaborative_room.html', {
        'room': room,
        'pieces_data': json.dumps(pieces_data),
        'player_role': player_role,
        'range_grid_size': range(grid_size),
        'grid_size': grid_size,
        'cell_size': cell_size,
        'container_size': container_size,
    })


@login_required
def create_jigsaw_room(request):
    if request.method == 'POST':
        form = JigsawPuzzleRoomForm(request.POST, request.FILES)
        if form.is_valid():
            puzzle_room = form.save(commit=False)
            puzzle_room.player1 = request.user
            puzzle_room.save()

            # Get the uploaded image
            image = Image.open(puzzle_room.puzzle_image.path)
            
            # Set grid size based on difficulty
            grid_size = {
                'easy': 4,
                'medium': 6,
                'hard': 8
            }[puzzle_room.difficulty]

            # Calculate piece size
            width, height = image.size
            piece_width = width // grid_size
            piece_height = height // grid_size

            # Create directory for pieces if it doesn't exist
            pieces_dir = os.path.join(settings.MEDIA_ROOT, 'puzzle_pieces')
            os.makedirs(pieces_dir, exist_ok=True)

            # Split image into pieces - Create two sets, one for each player
            for player_num in ['player1', 'player2']:  # Create pieces for both players
                for i in range(grid_size):
                    for j in range(grid_size):
                        # Crop piece from original image
                        left = j * piece_width
                        top = i * piece_height
                        right = left + piece_width
                        bottom = top + piece_height
                        
                        piece = image.crop((left, top, right, bottom))
                        
                        # Save piece with player-specific filename
                        piece_filename = f'piece_{puzzle_room.id}_{player_num}_{i}_{j}.png'
                        piece_path = os.path.join(pieces_dir, piece_filename)
                        piece.save(piece_path)

                        # Create piece record in database with player assignment
                        JigsawPuzzlePiece.objects.create(
                            room=puzzle_room,
                            image_piece=f'puzzle_pieces/{piece_filename}',
                            x_position=random.randint(0, 300),
                            y_position=random.randint(0, 300),
                            player_assignment=player_num  # Add this field to your model
                        )

            return redirect('waiting_room', room_id=puzzle_room.id)
    else:
        form = JigsawPuzzleRoomForm()
    return render(request, 'jigsaw_puzzle/create_room.html', {'form': form})


def save_puzzle_piece(piece_data):
    """Helper function to save puzzle piece."""
    fs = FileSystemStorage(location=os.path.join(settings.MEDIA_ROOT, 'jigsaw_pieces'))
    with open(piece_data['path'], 'rb') as piece_file:
        filename = fs.save(piece_data['file_name'], File(piece_file))
        return filename  # Return only the filename
@login_required
def waiting_room(request, room_id):
    room = get_object_or_404(JigsawPuzzleRoom, id=room_id)
    invite_link = request.build_absolute_uri(reverse('join_room', args=[room.id]))

    if room.player2 is None:
        return render(request, 'jigsaw_puzzle/waiting_room.html', {
            'room': room,
            'invite_link': invite_link,
        })
    else:
        return redirect('collaborative_room' if room.mode == 'collaborative' else 'jigsaw_puzzle_room', room_id=room.id)
    
def create_puzzle_pieces(image_path, difficulty):
    img = Image.open(image_path)
    width, height = img.size
    
    # Define the directory where pieces will be saved
    pieces_dir = os.path.join(settings.MEDIA_ROOT, 'jigsaw_pieces')
    
    # Ensure the directory exists
    if not os.path.exists(pieces_dir):
        os.makedirs(pieces_dir)

    pieces_per_row = {'easy': 4, 'medium': 6, 'hard': 8}[difficulty]
    piece_width = width // pieces_per_row
    piece_height = height // pieces_per_row
    piece_paths = []

    for i in range(pieces_per_row):
        for j in range(pieces_per_row):
            box = (
                j * piece_width, i * piece_height,
                (j + 1) * piece_width, (i + 1) * piece_height
            )
            piece = img.crop(box)
            
            # Generate a unique filename
            piece_filename = f'piece_{i}_{j}_{random.randint(0, 100000)}.png'
            
            # Save relative to MEDIA_ROOT
            relative_path = os.path.join('jigsaw_pieces', piece_filename)
            absolute_path = os.path.join(settings.MEDIA_ROOT, relative_path)
            
            # Save the image
            piece.save(absolute_path)
            
            # Randomize initial positions
            initial_x = random.randint(0, 350)
            initial_y = random.randint(0, 350)
            
            # Store the relative path that will work with MEDIA_URL
            piece_paths.append({
                'path': absolute_path,
                'file_name': relative_path,  # Store relative path
                'x': initial_x,
                'y': initial_y
            })
    
    return piece_paths


from django.http import JsonResponse

@login_required
def check_player2_status(request, room_id):
    room = get_object_or_404(JigsawPuzzleRoom, id=room_id)
    return JsonResponse({'player2_joined': room.player2 is not None})


@login_required
def join_room(request, room_id):
    room = get_object_or_404(JigsawPuzzleRoom, id=room_id)

    if room.player2 is None:
        room.player2 = request.user  # Set Player 2
        room.save()
        return redirect('collaborative_room' if room.mode == 'collaborative' else 'jigsaw_puzzle_room', room_id=room.id)
    else:
        return HttpResponse("This room is full.")

# In jigsaw_puzzle/views.py
@login_required
def jigsaw_puzzle_room(request, room_id):
    room = get_object_or_404(JigsawPuzzleRoom, id=room_id)
    player_role = 'player1' if request.user == room.player1 else 'player2'
    
    # Only get pieces assigned to the current player
    pieces = JigsawPuzzlePiece.objects.filter(
        room=room,
        player_assignment=player_role
    )
    
    pieces_data = []
    for piece in pieces:
        pieces_data.append({
            'id': piece.id,
            'image_url': piece.image_piece.url,
            'x': piece.x_position,
            'y': piece.y_position,
            'is_placed': piece.is_placed,
            'placed_by': piece.placed_by if hasattr(piece, 'placed_by') else None
        })

    return render(request, 'jigsaw_puzzle/puzzle_room.html', {
        'room': room,
        'pieces_data': json.dumps(pieces_data),
        'player_role': player_role,
        'player1': room.player1.username,
        'player2': room.player2.username if room.player2 else '',
    })


@login_required
def remove_piece(request, piece_id):
    """Handle removing a puzzle piece from the grid."""
    if request.method == 'POST':
        logger.debug(f"Attempting to remove piece with id {piece_id}")
        piece = get_object_or_404(JigsawPuzzlePiece, id=piece_id)
        try:
            # Instead of deleting, reset the position
            piece.x_position = -1
            piece.y_position = -1
            piece.save()
            
            # Notify all clients about the piece removal via WebSocket
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                f'puzzle_{piece.room.id}',
                {
                    'type': 'piece_remove',
                    'piece_id': piece_id
                }
            )
            
            return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)
