import json
import os
import random
from django.conf import settings
from django.core.files.storage import default_storage
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.decorators import login_required
from PIL import Image
from .models import PhysicsPuzzleRoom, PhysicsPuzzlePiece
from .forms import PhysicsPuzzleRoomForm

@login_required
def create_physics_room(request):
    """Handles image upload and creates physics puzzle pieces."""
    if request.method == 'POST':
        form = PhysicsPuzzleRoomForm(request.POST, request.FILES)
        if form.is_valid():
            puzzle_room = form.save(commit=False)
            puzzle_room.player1 = request.user
            puzzle_room.save()

            # ✅ Split the uploaded image into falling puzzle pieces
            split_image_into_pieces(puzzle_room)

            return redirect('physics_puzzle:physics_puzzle_room', room_id=puzzle_room.id)
    else:
        form = PhysicsPuzzleRoomForm()

    return render(request, 'physics_puzzle/create_room.html', {'form': form})

def split_image_into_pieces(room, grid_size=4):
    """Splits the uploaded puzzle image into physics-based tiles."""
    if not room.puzzle_image:
        print("❌ No puzzle image found!")
        return

    puzzle_pieces_dir = os.path.join(settings.MEDIA_ROOT, 'puzzle_pieces')
    os.makedirs(puzzle_pieces_dir, exist_ok=True)

    image_path = room.puzzle_image.path
    img = Image.open(image_path)
    width, height = img.size
    tile_width, tile_height = width // grid_size, height // grid_size

    for index in range(grid_size * grid_size):
        row, col = divmod(index, grid_size)
        box = (col * tile_width, row * tile_height, (col + 1) * tile_width, (row + 1) * tile_height)
        tile = img.crop(box)

        tile_filename = f'puzzle_pieces/{room.id}_{index}.png'
        tile_path = os.path.join(settings.MEDIA_ROOT, tile_filename)
        tile.save(tile_path, format='PNG')

        # ✅ Pieces start falling from the top
        PhysicsPuzzlePiece.objects.create(
            room=room,
            image_piece=tile_filename,
            initial_x=random.randint(100, 700),  # Random x start position
            initial_y=random.randint(-300, -50),  # Start **above the screen**
            correct_x=col * tile_width,
            correct_y=row * tile_height,
            is_placed=False
        )

@login_required
def physics_puzzle_room(request, room_id):
    """Loads the physics puzzle room."""
    room = get_object_or_404(PhysicsPuzzleRoom, id=room_id)
    pieces = PhysicsPuzzlePiece.objects.filter(room=room)

    pieces_data = [
        {
            'id': piece.id,
            'image_url': piece.image_piece.url,
            'x': piece.initial_x,
            'y': piece.initial_y,
            'correct_x': piece.correct_x,
            'correct_y': piece.correct_y,
            'is_placed': piece.is_placed
        }
        for piece in pieces
    ]

    return render(request, 'physics_puzzle/physics_room.html', {
        'room': room,
        'pieces_data': json.dumps(pieces_data)
    })
