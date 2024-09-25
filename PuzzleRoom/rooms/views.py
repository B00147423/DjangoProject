# rooms/views.py
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from .models import PuzzleRoom
from puzzles.models import Puzzle
from django.contrib.auth.decorators import login_required
import uuid
from puzzles.views import create_puzzle_and_split
from django.conf import settings
import json
from .models import PuzzleRoom
from puzzles.models import PuzzlePiece

@login_required
def create_room(request):
    if request.method == "POST":
        room_name = request.POST.get('roomName')
        difficulty = request.POST.get('difficulty')

        # Create the puzzle using puzzle logic (delegated to puzzles app)
        puzzle, piece_paths = create_puzzle_and_split(request.FILES['image'], difficulty)

        # Generate a unique room ID
        room_id = str(uuid.uuid4())

        # Create the puzzle room
        new_room = PuzzleRoom.objects.create(
            room_id=room_id,
            name=room_name,
            puzzle=puzzle,
            state={'pieces': piece_paths},  # Store piece paths in the room state
        )


        rows, cols = puzzle.rows, puzzle.cols
        for index, piece in enumerate(piece_paths):
            piece_paths = f'puzzles/{uuid.uuid4()}_piece_{index}.png'

            col = index % cols
            row = index //cols

            # Save each piece as a separate PuzzlePiece entry
            PuzzlePiece.objects.create(
                puzzle=puzzle,
                room=new_room,
                image_path=f'{settings.MEDIA_URL}{piece_paths}',
                original_col=col,
                original_row=row,
                current_col=None,  # Initially no piece is placed
                current_row=None,  # Initially no piece is placed
                is_correct=False,  # Initially, no piece is correct
            )
        # Assign the room to the user
        request.user.puzzle_room = new_room
        request.user.save()

        return JsonResponse({'room_id': room_id, 'status': 'success'})

    return render(request, 'rooms/create_room.html')

def room_detail(request, room_id):
    # Retrieve the room based on the room_id
    room = get_object_or_404(PuzzleRoom, room_id=room_id)

    # Calculate the range for rows and columns
    puzzle_pieces = PuzzlePiece.objects.filter(room=room)

    # Pass MEDIA_URL to template context
    context = {
        'room': room,
        'puzzle_pieces':puzzle_pieces,
        'MEDIA_URL': settings.MEDIA_URL,  # Pass the MEDIA_URL from settings
    }

    return render(request, 'rooms/room_detail.html', context)



def save_puzzle_state(request, room_id):
    if request.method == 'POST':
        room = PuzzleRoom.objects.get(room_id=room_id)
        data = json.loads(request.body)
        
        # Update the room's state with the new piece positions
        room.state['pieces'][data['pieceId']] = data['position']
        room.save()

        return JsonResponse({'status': 'success'})
    
    return JsonResponse({'error': 'Invalid request'}, status=400)
