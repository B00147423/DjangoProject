#C:\Users\beka\OneDrive\Desktop\Year4DjangoMajor-Project\DjangoProject\PuzzleRoom\jigsaw_puzzle\tests.py
import json
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from .models import JigsawPuzzleRoom, JigsawPuzzlePiece
from django.contrib.messages import get_messages
from unittest.mock import patch
from asgiref.testing import ApplicationCommunicator
User = get_user_model()
from unittest.mock import patch, MagicMock
from .models import JigsawPuzzleRoom
from .forms import JigsawPuzzleRoomForm
from django.core.files.uploadedfile import SimpleUploadedFile
class JigsawPuzzleModelTests(TestCase):
    def test_jigsaw_puzzle_room_creation(self):
        room = JigsawPuzzleRoom.objects.create(name="Test Room", difficulty="easy", mode="collaborative")
        self.assertEqual(room.name, "Test Room")
        self.assertEqual(room.difficulty, "easy")
        self.assertEqual(room.mode, "collaborative")
        self.assertIsNotNone(room.room_code)

    def test_jigsaw_puzzle_piece_creation(self):
        room = JigsawPuzzleRoom.objects.create(name="Test Room", difficulty="easy", mode="collaborative")
        piece = JigsawPuzzlePiece.objects.create(room=room, x_position=0, y_position=0)
        self.assertEqual(piece.room, room)
        self.assertEqual(piece.x_position, 0)
        self.assertEqual(piece.y_position, 0)


class JigsawPuzzleViewTests(TestCase):
    def setUp(self):
        # Create test user
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser', 
            email='test@example.com', 
            password='testpass123'
        )
        self.client.login(username='testuser', password='testpass123')

        # Create test image
        self.test_image = SimpleUploadedFile(
            name='test_image.jpg', 
            content=b'test image content', 
            content_type='image/jpeg'
        )
    def test_create_jigsaw_room_view(self):
        response = self.client.get(reverse("jigsaw_puzzle:create_jigsaw_room"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "jigsaw_puzzle/create_room.html")

    def test_collaborative_room_view(self):
        room = JigsawPuzzleRoom.objects.create(
            name="Test Room",
            difficulty="easy",
            mode="collaborative",
            player1=self.user
        )
        response = self.client.get(reverse("jigsaw_puzzle:collaborative_room", args=[room.id]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'jigsaw_puzzle/collaborative_room.html')

    def test_join_room_view(self):
        room = JigsawPuzzleRoom.objects.create(
            name="Test Room",
            difficulty="easy",
            mode="collaborative",
            player1=self.user
        )

        response = self.client.post(reverse('jigsaw_puzzle:join_room'), {'room_code': room.room_code})

        room.refresh_from_db()

        self.assertEqual(room.player2, self.user)
        self.assertEqual(response.status_code, 302)


    def test_waiting_room_view(self):
        room = JigsawPuzzleRoom.objects.create(
            name="Test Room",
            difficulty="easy",
            mode="collaborative",
            player1=self.user
        )
        response = self.client.get(reverse('jigsaw_puzzle:waiting_room', args=[room.id]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'jigsaw_puzzle/waiting_room.html')

    def test_puzzle_room_view(self):
        room = JigsawPuzzleRoom.objects.create(
            name="Test Room",
            difficulty="easy",
            mode="collaborative",
            player1=self.user
        )
        response = self.client.get(reverse('jigsaw_puzzle:jigsaw_puzzle_room', args=[room.id]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'jigsaw_puzzle/puzzle_room.html')

    def test_get_pieces(self):
        room = JigsawPuzzleRoom.objects.create(name="Test Room", difficulty="easy", mode="collaborative", player1=self.user)
        piece = JigsawPuzzlePiece.objects.create(room=room, x_position=0, y_position=0)
        
        response = self.client.get(reverse('jigsaw_puzzle:get_pieces') + f'?room_id={room.id}')
        self.assertEqual(response.status_code, 200)
        self.assertIn('pieces', response.json())
        self.assertEqual(len(response.json()['pieces']), 1)
        self.assertEqual(response.json()['pieces'][0]['id'], piece.id)

    def test_collaborative_room_unauthorized(self):
        room = JigsawPuzzleRoom.objects.create(name="Test Room", difficulty="easy", mode="collaborative")
        response = self.client.get(reverse('jigsaw_puzzle:collaborative_room', args=[room.id]))
        self.assertEqual(response.status_code, 302)  # Redirects to dashboard or login

    def test_update_piece_position(self):
        room = JigsawPuzzleRoom.objects.create(name="Test Room", difficulty="easy", mode="collaborative", player1=self.user)
        piece = JigsawPuzzlePiece.objects.create(room=room, x_position=0, y_position=0)
        
        data = {
            'piece_id': piece.id,
            'new_x': 10,
            'new_y': 20,
            'player_role': 'player1'
        }
        response = self.client.post(reverse('jigsaw_puzzle:update_piece_position'), json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        piece.refresh_from_db()
        self.assertEqual(piece.x_position, 10)
        self.assertEqual(piece.y_position, 20)
        self.assertTrue(piece.is_placed)

    def test_get_pieces_invalid_room(self):
        response = self.client.get(reverse('jigsaw_puzzle:get_pieces'))
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.json())
        self.assertEqual(response.json()['error'], 'Room ID is required.')

    def test_join_room_full(self):
        room = JigsawPuzzleRoom.objects.create(
            name="Test Room", difficulty="easy", mode="collaborative", player1=self.user
        )
        player2 = User.objects.create_user(username="player2", email="player2@example.com", password="12345")
        room.player2 = player2
        room.save()

        response = self.client.post(reverse('jigsaw_puzzle:join_room'), {'room_code': room.room_code})
        self.assertEqual(response.status_code, 302)
        
        messages = [m.message for m in get_messages(response.wsgi_request)]
        self.assertIn("This room is already full.", messages)

    def test_toggle_ready_status(self):
        room = JigsawPuzzleRoom.objects.create(name="Test Room", difficulty="easy", mode="collaborative", player1=self.user)
        data = {'ready': True}
        response = self.client.post(reverse('jigsaw_puzzle:toggle_ready_status', args=[room.id]), json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        room.refresh_from_db()
        self.assertTrue(room.player1_ready)

    def test_check_ready_status(self):
        room = JigsawPuzzleRoom.objects.create(name="Test Room", difficulty="easy", mode="collaborative", player1=self.user)
        room.player1_ready = True
        room.player2_ready = False
        room.save()

        response = self.client.get(reverse('jigsaw_puzzle:check_ready_status', args=[room.id]))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()['both_ready'])

    def test_create_room_missing_name(self):
        # Prepare room creation data with missing name
        room_data = {
            'name': '',
            'difficulty': 'easy',
            'mode': 'collaborative',
            'puzzle_image': self.test_image
        }
        
        # Submit the form
        response = self.client.post(
            reverse('jigsaw_puzzle:create_jigsaw_room'), 
            data=room_data
        )
        
        # Check form validation
        self.assertEqual(response.status_code, 200)
        
        # Check for form errors
        form = response.context['form']
        self.assertFalse(form.is_valid())
        
        # Check specific name field error
        self.assertIn('name', form.errors)
        self.assertEqual(
            form.errors['name'][0], 
            "This field is required."
        )

    def test_name_validation_form(self):
        # Test form validation directly
        form_data = {
            'name': '',
            'difficulty': 'easy',
            'mode': 'collaborative',
        }
        form = JigsawPuzzleRoomForm(data=form_data)
        
        # Validate form
        self.assertFalse(form.is_valid())
        
        # Check specific name field error
        self.assertIn('name', form.errors)
        self.assertEqual(
            form.errors['name'][0], 
            "This field is required."
        )

    def test_join_room_invalid_code(self):
        response = self.client.post(reverse("jigsaw_puzzle:join_room"), {'room_code': 'INVALID'})
        self.assertEqual(response.status_code, 302)  # Expect redirect
        messages = [m.message for m in get_messages(response.wsgi_request)]
        self.assertIn("Room not found. Please check the room code.", messages)

    
    def test_protected_view_no_login(self):
        self.client.logout()
        response = self.client.get(reverse("jigsaw_puzzle:collaborative_room", args=[1]))
        self.assertEqual(response.status_code, 302)  # Expect redirect to login
        self.assertIn("/user/auth/", response.url)  # Adjust to your login path



    def test_access_room_as_non_participant(self):
        room = JigsawPuzzleRoom.objects.create(
            name="Test Room", difficulty="easy", mode="collaborative", player1=self.user
        )
        new_user = User.objects.create_user(username="newuser", email="newuser@example.com", password="12345")
        self.client.force_login(new_user)
        response = self.client.get(reverse("jigsaw_puzzle:collaborative_room", args=[room.id]))
        self.assertEqual(response.status_code, 302)  # Redirects to an error page or dashboard
        self.assertIn(reverse("user:dashboard"), response.url)


    @patch('channels.layers.get_channel_layer')
    def test_update_piece_position_real_time(self, mock_channel_layer):
        # Create room and piece
        room = JigsawPuzzleRoom.objects.create(
            name="Test Room", 
            difficulty="easy", 
            mode="collaborative", 
            puzzle_image=self.test_image,
            player1=self.user
        )
        piece = JigsawPuzzlePiece.objects.create(
            room=room, 
            image_piece=self.test_image,
            x_position=0, 
            y_position=0
        )

        # Mock channel layer
        mock_group_send = MagicMock()
        mock_channel_layer.return_value = MagicMock(group_send=mock_group_send)

        # Prepare piece move data
        piece_data = {
            'piece_id': piece.id,
            'room_id': room.id,
            'new_x': 100,
            'new_y': 100
        }

        # Send piece position update
        response = self.client.post(
            reverse('jigsaw_puzzle:update_piece_position'), 
            data=json.dumps(piece_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)

    def test_join_full_room(self):
        room = JigsawPuzzleRoom.objects.create(name="Test Room", difficulty="easy", mode="collaborative", player1=self.user)
        player2 = User.objects.create_user(username="player2", email="player2@example.com", password="12345")
        room.player2 = player2
        room.save()
        
        new_user = User.objects.create_user(username="player3", email="player3@example.com", password="12345")
        self.client.force_login(new_user)
        response = self.client.post(reverse("jigsaw_puzzle:join_room"), {"room_code": room.room_code})
        self.assertEqual(response.status_code, 302)
        messages = [m.message for m in get_messages(response.wsgi_request)]
        self.assertIn("This room is already full.", messages)


    def test_update_piece_position_invalid_json(self):
        response = self.client.post(
            reverse("jigsaw_puzzle:update_piece_position"),
            data="Invalid JSON",
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("Invalid JSON data", response.json().get("message", ""))


class JigsawPuzzleUtilityTests(TestCase):
    def test_generate_unique_code(self):
        room = JigsawPuzzleRoom(name="Test Room", difficulty="easy", mode="collaborative")
        code = room.generate_unique_code()
        self.assertEqual(len(code), 8)
        self.assertTrue(code.isalnum())

