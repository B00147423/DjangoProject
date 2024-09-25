#C:\Users\beka\OneDrive\Desktop\Year4DjangoMajor-Project\DjangoProject\PuzzleRoom\puzzles\views.py

import json
from django.shortcuts import get_object_or_404, render
from puzzles.models import Puzzle
from puzzles.utils import split_image
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.conf import settings
import uuid
import os
from django.http import JsonResponse
from puzzles.models import Puzzle
from django.views.decorators.csrf import csrf_exempt
from rooms.models import PuzzleRoom 
from PIL import Image
from django.core.files.uploadedfile import InMemoryUploadedFile
import io


def create_puzzle_and_split(uploaded_image, difficulty):
    # Set the number of pieces based on difficulty
    if difficulty == 'easy':
        rows, cols = 2, 5  # 10 pieces total
    elif difficulty == 'medium':
        rows, cols = 3, 5  # 15 pieces
    else:
        rows, cols = 4, 5  # 20 pieces

    # Open the uploaded image using Pillow
    img = Image.open(uploaded_image)

    # Resize the image to 500x500
    img = img.resize((500, 500), Image.Resampling.LANCZOS)

    # Save the resized image to memory
    img_io = io.BytesIO()
    img.save(img_io, format='PNG')
    img_io.seek(0)

    # Create a new uploaded file object
    resized_image = InMemoryUploadedFile(
        img_io, None, f"{uploaded_image.name}_resized.png", 'image/png', img_io.getbuffer().nbytes, None
    )

    # Save the resized image using Django's storage
    image_name = default_storage.save(f'puzzles/{resized_image.name}', ContentFile(resized_image.read()))

    # Create the puzzle in the database
    puzzle = Puzzle.objects.create(
        title=f"Puzzle {str(uuid.uuid4())[:8]}",
        image=image_name,
        rows=rows,  # Set rows based on difficulty
        cols=cols   # Set cols based on difficulty
    )

    # Example scaling factor (no additional scaling after resizing to 500x500)
    pieces = split_image(default_storage.path(image_name), rows, cols)

    # Save each piece
    piece_paths = []
    for index, piece in enumerate(pieces):
        piece_path = f'puzzles/{uuid.uuid4()}_piece_{index}.png'
        piece.save(os.path.join(settings.MEDIA_ROOT, piece_path))  
        piece_paths.append(f'{settings.MEDIA_URL}{piece_path}')

    return puzzle, piece_paths




def save_puzzle_state(request, room_id):
    if request.method == 'POST':
        room = get_object_or_404(PuzzleRoom, room_id=room_id)
        data = json.loads(request.body)

        # Find the piece and update its state in the room
        piece_index = data['piece_id']
        new_col = data['col_target']
        new_row = data['row_target']

        room.state['pieces'][piece_index]['current_col'] = new_col
        room.state['pieces'][piece_index]['current_row'] = new_row
        room.save()

        return JsonResponse({'status': 'success'})
    
    return JsonResponse({'error': 'Invalid request'}, status=400)

