# Standard Library
import os
import random
import string
import json
from datetime import timedelta
from asyncio.log import logger
from cProfile import Profile

# Django Core
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.urls import reverse
from django.core.files import File
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone

# Django Models
from django.contrib.auth import get_user_model
from django.contrib.auth.models import User
from .models import JigsawPuzzleRoom, JigsawPuzzlePiece, Leaderboard, ChatMessage

# Forms
from .forms import JigsawPuzzleRoomForm

# Image Processing
from PIL import Image, ImageChops

# Channels/Async
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

@login_required
def get_remaining_time(request, room_id):
    room = get_object_or_404(JigsawPuzzleRoom, id=room_id)
    remaining = room.get_remaining_time()
    return JsonResponse({'remaining_time': remaining})

@login_required
def get_pieces(request):
    room_id = request.GET.get('room_id')
    if not room_id:
        return JsonResponse({'error': 'Room ID is required.'}, status=400)

    try:
        room = JigsawPuzzleRoom.objects.get(id=room_id)
    except JigsawPuzzleRoom.DoesNotExist:
        return JsonResponse({'error': 'Room not found.'}, status=404)

    pieces = JigsawPuzzlePiece.objects.filter(room=room)
    pieces_data = [
        {
            'id': piece.id,
            'x': piece.x_position,
            'y': piece.y_position,
            'is_placed': piece.is_placed,
            'image_url': piece.image_piece.url if piece.image_piece else '',
            'placed_by': piece.placed_by,
            'grid_x': piece.grid_x,
            'grid_y': piece.grid_y,
        }
        for piece in pieces
    ]
    return JsonResponse({'pieces': pieces_data})


@login_required
def collaborative_jigsaw_room(request, room_id):
    room = get_object_or_404(JigsawPuzzleRoom, id=room_id)
    pieces = JigsawPuzzlePiece.objects.filter(room=room)

    if request.user == room.player1:
        player_role = 'player1'
    elif request.user == room.player2:
        player_role = 'player2'
    else:
        return redirect('user:dashboard')

    pieces_data = [
        {
            'image_url': piece.image_piece.url if piece.image_piece else None,
            'x': piece.x_position,
            'y': piece.y_position,
            'initial_x': piece.initial_x,
            'initial_y': piece.initial_y,
            'id': piece.id,
            'is_placed': piece.is_placed,
            'placed_by': piece.placed_by,
            'grid_x': piece.grid_x,
            'grid_y': piece.grid_y,
        }
        for piece in pieces if piece.image_piece  # Only include pieces with valid images
    ]

    chat_messages = [
        {'username': msg.user.username, 'message': msg.message}
        for msg in ChatMessage.objects.filter(room=room).order_by('timestamp')
    ]

    grid_size = {
        'easy': 4,
        'medium': 6,
        'hard': 8
    }.get(room.difficulty, 4)

    cell_size = 400 // grid_size
    container_size = 400

    return render(request, 'jigsaw_puzzle/collaborative_room.html', {
        'room': room,
        'pieces_data': json.dumps(pieces_data),
        'player_role': player_role,
        'range_grid_size': range(grid_size),
        'grid_size': grid_size,
        'cell_size': cell_size,
        'container_size': container_size,
        'participants': [room.player1, room.player2], 
        'full_image_url': room.puzzle_image.url,
        'chat_messages': json.dumps(chat_messages),
    })

@csrf_exempt
@login_required
def update_piece_position(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON data'}, status=400)

        piece_id = data.get('piece_id')
        new_x = data.get('new_x')
        new_y = data.get('new_y')
        player_role = data.get('player_role')

        piece = get_object_or_404(JigsawPuzzlePiece, id=piece_id)
        piece.x_position = new_x
        piece.y_position = new_y
        piece.is_placed = True
        piece.placed_by = player_role
        piece.save()

        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f'puzzle_room_{piece.room.id}',
            {
                'type': 'piece_move',
                'piece_id': piece.id,
                'new_x': new_x,
                'new_y': new_y,
                'player_role': player_role,
            }
        )

        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)

def generate_room_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

@login_required
def create_jigsaw_room(request):
    if request.method == 'POST':
        form = JigsawPuzzleRoomForm(request.POST, request.FILES)
        if form.is_valid():
            puzzle_room = form.save(commit=False)
            puzzle_room.player1 = request.user
            puzzle_room.save()
            puzzle_room.room_code = generate_room_code()

            # Get the uploaded image
            image = Image.open(puzzle_room.puzzle_image.path)

            # Set grid size based on difficulty
            grid_sizes = {'easy': 4, 'medium': 6, 'hard': 8}
            grid_size = grid_sizes[puzzle_room.difficulty]

            # Calculate piece size based on image dimensions
            width, height = image.size
            piece_width = width // grid_size
            piece_height = height // grid_size

            # Create directory for pieces if it doesn't exist
            pieces_dir = os.path.join(settings.MEDIA_ROOT, 'puzzle_pieces')
            os.makedirs(pieces_dir, exist_ok=True)

            # Calculate container size and base grid size consistently with frontend
            container_size = min(800, int(width * 0.9))  # Use 90% of image width, capped at 800px for larger screens
            base_grid_size = container_size // grid_size  # This will give us proportional sizes for each difficulty

            if puzzle_room.mode == 'collaborative':
                # Create one set of pieces for collaborative mode
                for i in range(grid_size):
                    for j in range(grid_size):
                        left = j * piece_width
                        top = i * piece_height
                        right = left + piece_width
                        bottom = top + piece_height

                        piece = image.crop((left, top, right, bottom))

                        piece_filename = f'piece_{puzzle_room.id}_{i}_{j}.png'
                        piece_path = os.path.join(pieces_dir, piece_filename)
                        
                        piece.save(piece_path, 'PNG')

                        grid_x = j
                        grid_y = i

                        # Create the puzzle piece in the database
                        JigsawPuzzlePiece.objects.create(
                            room=puzzle_room,
                            image_piece=f'puzzle_pieces/{piece_filename}',
                            x_position=random.randint(0, container_size - base_grid_size),  
                            y_position=random.randint(0, container_size - base_grid_size), 
                            initial_x=random.randint(0, container_size - base_grid_size),
                            initial_y=random.randint(0, container_size - base_grid_size),
                            grid_x=grid_x, 
                            grid_y=grid_y,
                        )
            else:
                # Create two sets of pieces for 1v1 mode
                for player_num in ['player1', 'player2']:
                    for i in range(grid_size):
                        for j in range(grid_size):
                            left = j * piece_width
                            top = i * piece_height
                            right = left + piece_width
                            bottom = top + piece_height

                            piece = image.crop((left, top, right, bottom))

                            piece_filename = f'piece_{puzzle_room.id}_{player_num}_{i}_{j}.png'
                            piece_path = os.path.join(pieces_dir, piece_filename)
                            
                            piece.save(piece_path, 'PNG')
                            grid_x = j
                            grid_y = i  

                            # Create the puzzle piece in the database
                            JigsawPuzzlePiece.objects.create(
                                room=puzzle_room,
                                image_piece=f'puzzle_pieces/{piece_filename}',
                                x_position=random.randint(0, container_size - base_grid_size),
                                y_position=random.randint(0, container_size - base_grid_size),
                                initial_x=left,
                                initial_y=top,
                                grid_x=grid_x,
                                grid_y=grid_y,
                                player_assignment=player_num,
                            )

            return redirect('jigsaw_puzzle:waiting_room', room_id=puzzle_room.id)
    else:
        form = JigsawPuzzleRoomForm()
    return render(request, 'jigsaw_puzzle/create_room.html', {'form': form})

@csrf_exempt
@login_required
def create_room_with_image(request):
    if request.method == 'POST':
        image_path = request.POST.get('image_path')  # e.g. 'jigsaw_puzzle/predefined_images/puppy.jpg'
        difficulty = request.POST.get('difficulty', 'easy')
        mode = request.POST.get('mode', 'collaborative')

        room = JigsawPuzzleRoom.objects.create(
            player1=request.user,
            difficulty=difficulty,
            mode=mode,
            puzzle_image=image_path,
        )

        # Get the base name of the image (e.g. 'puppy')
        base_name = os.path.splitext(os.path.basename(image_path))[0]
        grid_sizes = {'easy': 4, 'medium': 6, 'hard': 8}
        grid_size = grid_sizes[difficulty]

        # Path to the pre-split pieces
        pieces_dir = os.path.join(
            settings.BASE_DIR, 'jigsaw_puzzle', 'static', 'jigsaw_puzzle', 'predefined_pieces', f"{base_name}_{difficulty}"
        )

        container_size = 400  # or whatever you use
        base_grid_size = container_size // grid_size

        if mode == 'collaborative':
            for i in range(grid_size):
                for j in range(grid_size):
                    piece_filename = f"{i}_{j}.png"
                    # The path relative to MEDIA_ROOT
                    static_piece_path = f"predefined_pieces/{base_name}_{difficulty}/{piece_filename}"
                    JigsawPuzzlePiece.objects.create(
                        room=room,
                        image_piece=static_piece_path,
                        x_position=random.randint(0, container_size - base_grid_size),
                        y_position=random.randint(0, container_size - base_grid_size),
                        initial_x=random.randint(0, container_size - base_grid_size),
                        initial_y=random.randint(0, container_size - base_grid_size),
                        grid_x=j,
                        grid_y=i,
                    )
        else:
            for player_num in ['player1', 'player2']:
                for i in range(grid_size):
                    for j in range(grid_size):
                        piece_filename = f"{i}_{j}.png"
                        static_piece_path = f"predefined_pieces/{base_name}_{difficulty}/{piece_filename}"
                        JigsawPuzzlePiece.objects.create(
                            room=room,
                            image_piece=static_piece_path,
                            x_position=random.randint(0, container_size - base_grid_size),
                            y_position=random.randint(0, container_size - base_grid_size),
                            initial_x=0,
                            initial_y=0,
                            grid_x=j,
                            grid_y=i,
                            player_assignment=player_num,
                        )

        return redirect('jigsaw_puzzle:waiting_room', room_id=room.id)
    return redirect('jigsaw_puzzle:choose_puzzle')

def save_puzzle_piece(piece_data):
    """Helper function to save puzzle piece."""
    fs = FileSystemStorage(location=os.path.join(settings.MEDIA_ROOT, 'jigsaw_pieces'))
    with open(piece_data['path'], 'rb') as piece_file:
        filename = fs.save(piece_data['file_name'], File(piece_file))
        return filename 
    
@login_required
def waiting_room(request, room_id):
    room = get_object_or_404(JigsawPuzzleRoom, id=room_id)
    invite_link = request.build_absolute_uri(reverse('jigsaw_puzzle:join_room'))

   
    if room.player1_ready and room.player2_ready:
        return redirect(
            'jigsaw_puzzle:collaborative_room' if room.mode == 'collaborative' else 'jigsaw_puzzle:jigsaw_puzzle_room',
            room_id=room.id,
        )

    
    player_role = 'player1' if request.user == room.player1 else 'player2' if request.user == room.player2 else None

    
    js_context = json.dumps({
        'room': {
            'id': room.id,
            'room_code': room.room_code,
            'mode': room.mode,
        },
        'player_role': player_role,
        'redirect_url': reverse(
            'jigsaw_puzzle:collaborative_room' if room.mode == 'collaborative' else 'jigsaw_puzzle:jigsaw_puzzle_room',
            args=[room.id]
        )
    })

    
    return render(request, 'jigsaw_puzzle/waiting_room.html', {
        'room': room,
        'invite_link': invite_link,
        'player_role': player_role,
        'player1_ready': room.player1_ready,
        'player2_ready': room.player2_ready,
        'js_context': js_context, 
    })

def create_puzzle_pieces(image_path, difficulty):
    img = Image.open(image_path)
    width, height = img.size
    
    pieces_dir = os.path.join(settings.MEDIA_ROOT, 'jigsaw_pieces')
    
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
            
           
            piece_filename = f'piece_{i}_{j}_{random.randint(0, 100000)}.png'
            
            
            relative_path = os.path.join('jigsaw_pieces', piece_filename)
            absolute_path = os.path.join(settings.MEDIA_ROOT, relative_path)
            
            
            piece.save(absolute_path)
            
           
            initial_x = random.randint(0, 350)
            initial_y = random.randint(0, 350)
            
            
            piece_paths.append({
                'path': absolute_path,
                'file_name': relative_path,
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
def join_room(request):
    if request.method == "POST":
        room_code = request.POST.get("room_code")
        if not room_code:
            messages.error(request, "Room code is required.")
            return redirect('user:dashboard')
        try:
            room = JigsawPuzzleRoom.objects.get(room_code=room_code)
            if room.player2 is None:
                room.player2 = request.user
                room.save()
                # Redirect to the waiting room
                return redirect('jigsaw_puzzle:waiting_room', room_id=room.id)
            else:
                messages.error(request, "This room is already full.")
        except JigsawPuzzleRoom.DoesNotExist:
            messages.error(request, "Room not found. Please check the room code.")
    return redirect('user:dashboard')




@login_required
def jigsaw_puzzle_room(request, room_id):
    room = get_object_or_404(JigsawPuzzleRoom, id=room_id)
    player_role = 'player1' if request.user == room.player1 else 'player2'
    
    
    pieces = JigsawPuzzlePiece.objects.filter(room=room)
    
    pieces_data = []
    for piece in pieces:
        pieces_data.append({
            'id': piece.id,
            'image_url': piece.image_piece.url,
            'x_position': piece.x_position,
            'y_position': piece.y_position,
            'is_placed': piece.is_placed,
            'placed_by': piece.placed_by,
            'grid_x': piece.grid_x,
            'grid_y': piece.grid_y,
            'is_correct': piece.is_correct,
            'player_assignment': piece.player_assignment
        })

    return render(request, 'jigsaw_puzzle/puzzle_room.html', {
        'room': room,
        'pieces_data': json.dumps(pieces_data),
        'player_role': player_role,
        'player1': room.player1.username,
        'player2': room.player2.username if room.player2 else '',
    })

@csrf_exempt
@login_required
def remove_piece(request, piece_id):
    if request.method == 'POST':
        piece = get_object_or_404(JigsawPuzzlePiece, id=piece_id)
       
        piece.x_position = piece.initial_x
        piece.y_position = piece.initial_y
        piece.is_placed = False
        piece.save()
        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)

from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
import json
from .models import JigsawPuzzleRoom

@csrf_exempt
@login_required
def toggle_ready_status(request, room_id):
    """
    Toggle the ready status of the current player in the specified room.
    If both players are ready, start the game and send the status to the frontend.
    """
    if request.method == 'POST':
        # Fetch the room object
        room = get_object_or_404(JigsawPuzzleRoom, id=room_id)

        try:
            # Parse the request body
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON data'}, status=400)

        # Update the ready status of the current player
        if request.user == room.player1:
            room.player1_ready = data.get('ready', False)
        elif request.user == room.player2:
            room.player2_ready = data.get('ready', False)
        else:
            return JsonResponse({'status': 'error', 'message': 'User not associated with this room'}, status=403)

        # Save the room with updated readiness status
        room.save()

        # Check if both players are ready
        both_ready = room.player1_ready and room.player2_ready
        message = "Both players are ready!" if both_ready else "Waiting for both players to be ready..."

        if both_ready:
            # Start the game if both players are ready
            room.start_game()  # Set the start_time for the game timer
            redirect_url = reverse('jigsaw_puzzle:jigsaw_puzzle_room', args=[room.id])
        else:
            redirect_url = None  # No redirection if players are not ready

        # Respond with readiness status and message
        return JsonResponse({
            'status': 'success',
            'message': message,
            'both_ready': both_ready,
            'redirect_url': redirect_url
        })

    # Handle non-POST requests
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)


    
@login_required
def check_ready_status(request, room_id):
    room = get_object_or_404(JigsawPuzzleRoom, id=room_id)
    both_ready = room.player1_ready and room.player2_ready
    message = "Both players are ready!" if both_ready else "Waiting for both players to be ready..."
    redirect_url = reverse('jigsaw_puzzle:jigsaw_puzzle_room', args=[room.id])
    return JsonResponse({'message': message, 'both_ready': both_ready, 'redirect_url': redirect_url})
from django.shortcuts import render, redirect
from django.urls import reverse
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
# Get the custom User model
User = get_user_model()
import random
import string
from .models import ChatMessage

@login_required
def get_remaining_time(request, room_id):
    room = get_object_or_404(JigsawPuzzleRoom, id=room_id)
    remaining = room.get_remaining_time()
    return JsonResponse({'remaining_time': remaining})

@login_required
def get_pieces(request):
    room_id = request.GET.get('room_id')
    if not room_id:
        return JsonResponse({'error': 'Room ID is required.'}, status=400)

    try:
        room = JigsawPuzzleRoom.objects.get(id=room_id)
    except JigsawPuzzleRoom.DoesNotExist:
        return JsonResponse({'error': 'Room not found.'}, status=404)

    pieces = JigsawPuzzlePiece.objects.filter(room=room)
    pieces_data = [
        {
            'id': piece.id,
            'x': piece.x_position,
            'y': piece.y_position,
            'is_placed': piece.is_placed,
            'image_url': piece.image_piece.url if piece.image_piece else '',
            'placed_by': piece.placed_by,
            'grid_x': piece.grid_x,
            'grid_y': piece.grid_y,
        }
        for piece in pieces
    ]
    return JsonResponse({'pieces': pieces_data})


@csrf_exempt
@login_required
def update_piece_position(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON data'}, status=400)

        piece_id = data.get('piece_id')
        new_x = data.get('new_x')
        new_y = data.get('new_y')
        player_role = data.get('player_role')

        piece = get_object_or_404(JigsawPuzzlePiece, id=piece_id)
        piece.x_position = new_x
        piece.y_position = new_y
        piece.is_placed = True
        piece.placed_by = player_role
        piece.save()

        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f'puzzle_room_{piece.room.id}',
            {
                'type': 'piece_move',
                'piece_id': piece.id,
                'new_x': new_x,
                'new_y': new_y,
                'player_role': player_role,
            }
        )

        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)

def generate_room_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

def generate_test_data():
    difficulties = ["easy", "medium", "hard"]
    modes = ["versus", "collaborative"]
    test_data = []

    for difficulty in difficulties:
        for mode in modes:
            for i in range(1, 51):  # Generate 50 entries for each combination
                completion_time = random.randint(60, 600)  # Random completion time between 60 and 600 seconds
                moves_taken = random.randint(30, 200)  # Random moves between 30 and 200
                created_at = timezone.now() - timedelta(days=random.randint(1, 365))  # Random creation date within the last year

                # Create a JigsawPuzzleRoom instance
                entry = JigsawPuzzleRoom(
                    mode=mode,
                    difficulty=difficulty,
                    completed=True,
                    completion_time=completion_time,
                    moves_taken=moves_taken,
                    created_at=created_at,
                    # Add other required fields here (e.g., players, winner, etc.)
                )
                test_data.append(entry)

    # Bulk create all entries
    JigsawPuzzleRoom.objects.bulk_create(test_data)

def leaderboard(request):
    difficulties = ["easy", "medium", "hard"]  # Define difficulty levels

    # Create separate queries for each difficulty level
    leaderboard_data = {
        difficulty: {
            "1v1": JigsawPuzzleRoom.objects.filter(mode='versus', completed=True, difficulty=difficulty).order_by('completion_time'),
            "collaboration": JigsawPuzzleRoom.objects.filter(mode='collaborative', completed=True, difficulty=difficulty).order_by('completion_time')
        }
        for difficulty in difficulties
    }

    # Count total entries for each difficulty and mode
    difficulty_counts = {
        difficulty: {
            "1v1": leaderboard_data[difficulty]["1v1"].count(),
            "collaboration": leaderboard_data[difficulty]["collaboration"].count()
        }
        for difficulty in difficulties
    }

    context = {
        "leaderboard_data": leaderboard_data,
        "difficulty_counts": difficulty_counts,
    }

    return render(request, "jigsaw_puzzle/leaderboard.html", context)

def save_puzzle_piece(piece_data):
    """Helper function to save puzzle piece."""
    fs = FileSystemStorage(location=os.path.join(settings.MEDIA_ROOT, 'jigsaw_pieces'))
    with open(piece_data['path'], 'rb') as piece_file:
        filename = fs.save(piece_data['file_name'], File(piece_file))
        return filename 
    
@login_required
def waiting_room(request, room_id):
    room = get_object_or_404(JigsawPuzzleRoom, id=room_id)
    invite_link = request.build_absolute_uri(reverse('jigsaw_puzzle:join_room'))

    # Redirect if both players are ready
    if room.player1_ready and room.player2_ready:
        return redirect(
            'jigsaw_puzzle:collaborative_room' if room.mode == 'collaborative' else 'jigsaw_puzzle:jigsaw_puzzle_room',
            room_id=room.id,
        )

    # Determine the player's role
    player_role = 'player1' if request.user == room.player1 else 'player2' if request.user == room.player2 else None

    # JSON context for JavaScript
    js_context = json.dumps({
        'room': {
            'id': room.id,
            'room_code': room.room_code,
            'mode': room.mode,
        },
        'player_role': player_role,
        'redirect_url': reverse(
            'jigsaw_puzzle:collaborative_room' if room.mode == 'collaborative' else 'jigsaw_puzzle:jigsaw_puzzle_room',
            args=[room.id]
        )
    })

    # Render waiting room template
    return render(request, 'jigsaw_puzzle/waiting_room.html', {
        'room': room,
        'invite_link': invite_link,
        'player_role': player_role,
        'player1_ready': room.player1_ready,
        'player2_ready': room.player2_ready,
        'js_context': js_context,  # Pass serialized JSON to the template
    })

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
def join_room(request):
    if request.method == "POST":
        room_code = request.POST.get("room_code")
        if not room_code:
            messages.error(request, "Room code is required.")
            return redirect('user:dashboard')
        try:
            room = JigsawPuzzleRoom.objects.get(room_code=room_code)
            if room.player2 is None:
                room.player2 = request.user
                room.save()
                # Redirect to the waiting room
                return redirect('jigsaw_puzzle:waiting_room', room_id=room.id)
            else:
                messages.error(request, "This room is already full.")
        except JigsawPuzzleRoom.DoesNotExist:
            messages.error(request, "Room not found. Please check the room code.")
    return redirect('user:dashboard')



# In jigsaw_puzzle/views.py
@login_required
def jigsaw_puzzle_room(request, room_id):
    room = get_object_or_404(JigsawPuzzleRoom, id=room_id)
    player_role = 'player1' if request.user == room.player1 else 'player2'
    
    # Get ALL pieces from the room, not just the current player's pieces
    pieces = JigsawPuzzlePiece.objects.filter(room=room)
    
    pieces_data = []
    for piece in pieces:
        pieces_data.append({
            'id': piece.id,
            'image_url': piece.image_piece.url,
            'x_position': piece.x_position,
            'y_position': piece.y_position,
            'is_placed': piece.is_placed,
            'placed_by': piece.placed_by,
            'grid_x': piece.grid_x,
            'grid_y': piece.grid_y,
            'is_correct': piece.is_correct,
            'player_assignment': piece.player_assignment
        })

    return render(request, 'jigsaw_puzzle/puzzle_room.html', {
        'room': room,
        'pieces_data': json.dumps(pieces_data),
        'player_role': player_role,
        'player1': room.player1.username,
        'player2': room.player2.username if room.player2 else '',
    })

@csrf_exempt
@login_required
def remove_piece(request, piece_id):
    if request.method == 'POST':
        piece = get_object_or_404(JigsawPuzzlePiece, id=piece_id)
        # Reset the piece position
        piece.x_position = piece.initial_x
        piece.y_position = piece.initial_y
        piece.is_placed = False
        piece.save()
        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)

from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
import json
from .models import JigsawPuzzleRoom

@csrf_exempt
@login_required
def toggle_ready_status(request, room_id):
    """
    Toggle the ready status of the current player in the specified room.
    If both players are ready, start the game and send the status to the frontend.
    """
    if request.method == 'POST':
        # Fetch the room object
        room = get_object_or_404(JigsawPuzzleRoom, id=room_id)

        try:
            # Parse the request body
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON data'}, status=400)

        # Update the ready status of the current player
        if request.user == room.player1:
            room.player1_ready = data.get('ready', False)
        elif request.user == room.player2:
            room.player2_ready = data.get('ready', False)
        else:
            return JsonResponse({'status': 'error', 'message': 'User not associated with this room'}, status=403)

        # Save the room with updated readiness status
        room.save()

        # Check if both players are ready
        both_ready = room.player1_ready and room.player2_ready
        message = "Both players are ready!" if both_ready else "Waiting for both players to be ready..."

        if both_ready:
            # Start the game if both players are ready
            room.start_game()  # Set the start_time for the game timer
            redirect_url = reverse('jigsaw_puzzle:jigsaw_puzzle_room', args=[room.id])
        else:
            redirect_url = None  # No redirection if players are not ready

        # Respond with readiness status and message
        return JsonResponse({
            'status': 'success',
            'message': message,
            'both_ready': both_ready,
            'redirect_url': redirect_url
        })

    # Handle non-POST requests
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)

def shuffle_pieces(room):
    # Get all pieces for the room
    pieces = list(JigsawPuzzlePiece.objects.filter(room=room))
    
    # Shuffle the pieces
    random.shuffle(pieces)
    
    for index, piece in enumerate(pieces):
        piece.initial_x = random.randint(0, 300)
        piece.initial_y = random.randint(0, 300)
        piece.save()

    # Return the shuffled pieces
    return pieces
    
@login_required
def check_ready_status(request, room_id):
    room = get_object_or_404(JigsawPuzzleRoom, id=room_id)
    both_ready = room.player1_ready and room.player2_ready
    message = "Both players are ready!" if both_ready else "Waiting for both players to be ready..."
    redirect_url = reverse('jigsaw_puzzle:jigsaw_puzzle_room', args=[room.id])
    return JsonResponse({'message': message, 'both_ready': both_ready, 'redirect_url': redirect_url})


@login_required
def completed_puzzles(request):
    completed_rooms = JigsawPuzzleRoom.objects.filter(completed=True).select_related('player1', 'player2')
    return render(request, 'jigsaw_puzzle/completed_puzzles.html', {'completed_rooms': completed_rooms})

@login_required
def choose_puzzle(request):
    images_dir = os.path.join(
        settings.BASE_DIR, 'jigsaw_puzzle', 'static', 'jigsaw_puzzle', 'predefined_images'
    )
    image_files = [f for f in os.listdir(images_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
    image_urls = [f'jigsaw_puzzle/predefined_images/{img}' for img in image_files]
    return render(request, 'jigsaw_puzzle/choose_puzzle.html', {'image_urls': image_urls})