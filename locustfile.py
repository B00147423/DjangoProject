from locust import HttpUser, task, between, SequentialTaskSet
import random
import string
import json
import re
import logging
from PIL import Image, ImageDraw
import io
import time
from itertools import product

# Keep your original logging setup
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class JigsawPuzzleUser(HttpUser):
    wait_time = between(1, 3)
    host = "http://localhost:8000"

    # Preserved your original CSRF extraction
    def _extract_csrf(self, response):
        """Extract CSRF token from response"""
        match = re.search(r"name=['\"]csrfmiddlewaretoken['\"] value=['\"](.+?)['\"]", response.text)
        if match:
            return match.group(1)
        return ""

    # Enhanced but kept your image generation concept
    def generate_test_image(self, size=(100, 100)):
        """Generate valid test image while preserving your style"""
        img = Image.new('RGB', size, color='red')
        draw = ImageDraw.Draw(img)
        draw.text((10,10), "TEST", fill='white')  # Add text to ensure valid image
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='PNG')
        img_byte_arr.seek(0)
        return img_byte_arr

    # Preserved your on_start with small reliability improvements
    def on_start(self):
        self.username = f"testuser_{random.randint(1, 100000)}"
        self.email = f"{self.username}@example.com"
        self.password = "testpass123"
        self.room_id = None
        self.room_code = None

        resp = self.client.get("/user/auth/")
        csrf_token = self._extract_csrf(resp)

        if not csrf_token:
            logger.error("Failed to get CSRF token")
            return

        with self.client.post("/user/auth/",
                data={
                    "username": self.username,
                    "email": self.email,
                    "password1": self.password,
                    "password2": self.password,
                    "csrfmiddlewaretoken": csrf_token
                },
                headers={"Referer": f"{self.host}/user/auth/"},
                catch_response=True) as response:

            if response.status_code != 200:
                response.failure(f"Registration failed: {response.text}")
                return
            self.session_cookies = response.cookies

        with self.client.post("/user/auth/",
                data={
                    "email": self.email,
                    "password": self.password,
                    "csrfmiddlewaretoken": csrf_token
                },
                headers={"Referer": f"{self.host}/user/auth/"},
                cookies=self.session_cookies,
                catch_response=True) as response:

            if response.status_code != 200:
                response.failure(f"Login failed: {response.text}")
            else:
                self.session_cookies.update(response.cookies) 

        # Preserved your original login
        with self.client.post("/user/auth/",
                data={
                    "email": self.email,
                    "password": self.password,
                    "csrfmiddlewaretoken": csrf_token
                },
                headers={"Referer": f"{self.host}/user/auth/"},
                cookies=self.session_cookies,
                catch_response=True) as response:
            
            if response.status_code != 200:
                response.failure(f"Login failed: {response.text}")

    @task
    def create_all_combinations(self):
        # Only run this once per user
        if hasattr(self, "created_combinations"):
            return
        self.created_combinations = True

        difficulties = ["easy", "medium", "hard"]
        modes = ["collaborative", "versus"]

        for difficulty, mode in product(difficulties, modes):
            resp = self.client.get("/jigsaw/create_room/jigsaw/")
            csrf_token = self._extract_csrf(resp)
            if not csrf_token:
                logger.error("Failed to get CSRF token for room creation")
                continue

            test_image = self.generate_test_image()
            data = {
                "name": f"Room {difficulty} {mode} {random.randint(1, 10000)}",
                "difficulty": difficulty,
                "mode": mode,
                "csrfmiddlewaretoken": csrf_token
            }
            files = {
                "puzzle_image": ("test.png", test_image.getvalue(), "image/png")
            }

            with self.client.post("/jigsaw/create_room/jigsaw/",
                    data=data,
                    files=files,
                    headers={
                        "Referer": f"{self.host}/jigsaw/create_room/jigsaw/",
                        "X-CSRFToken": csrf_token
                    },
                    allow_redirects=False,
                    catch_response=True) as response:

                if response.status_code == 302:
                    logger.info(f"Created room for {difficulty} {mode}")
                else:
                    logger.error(f"Failed to create room: {difficulty} {mode} | {response.status_code} | {response.text[:200]}")

    # FIXED VERSION OF YOUR create_and_join_room (minimal changes)
    @task(3)
    def create_and_join_room(self):
        resp = self.client.get("/jigsaw/create_room/jigsaw/")
        csrf_token = self._extract_csrf(resp)

        if not csrf_token:
            logger.error("Failed to get CSRF token for room creation")
            return

        test_image = self.generate_test_image()
        room_name = f"Room {random.randint(1, 10000)}"
        difficulty = random.choice(["easy", "medium", "hard"])
        mode = random.choice(["collaborative", "versus"])

        data = {
            "name": room_name,
            "difficulty": difficulty,
            "mode": mode,
            "csrfmiddlewaretoken": csrf_token
        }
        files = {
            "puzzle_image": ("test.png", test_image.getvalue(), "image/png")
        }

        with self.client.post("/jigsaw/create_room/jigsaw/",
                data=data,
                files=files,
                headers={
                    "Referer": f"{self.host}/jigsaw/create_room/jigsaw/",
                    "X-CSRFToken": csrf_token
                },
                allow_redirects=False,
                catch_response=True) as response:

            if response.status_code == 302:
                redirect_url = response.headers.get('Location', '')
                if "/waiting-room/" in redirect_url:
                    self.room_id = int(redirect_url.strip('/').split('/')[-1])
                else:
                    response.failure(f"Unexpected redirect URL: {redirect_url}")
                    return
            else:
                response.failure(f"Unexpected status (no redirect): {response.status_code} {response.text[:200]}")

        # PRESERVED YOUR ORIGINAL JOIN LOGIC
        if self.room_id:
            # Get room code from waiting room
            with self.client.get(f"/jigsaw/waiting-room/{self.room_id}/",
                               catch_response=True) as response:
                if response.status_code == 200:
                    match = re.search(r"room_code['\"]?:\s*['\"]([A-Z0-9]{8})['\"]", response.text)
                    if match:
                        self.room_code = match.group(1)

            if self.room_code:
                # Get CSRF token for join page
                join_resp = self.client.get("/jigsaw/join_room/")
                join_csrf = self._extract_csrf(join_resp)
                
                with self.client.post("/jigsaw/join_room/",
                                    data={
                                        "room_code": self.room_code,
                                        "csrfmiddlewaretoken": join_csrf
                                    },
                                    headers={
                                        "Referer": f"{self.host}/jigsaw/join_room/",
                                        "X-CSRFToken": join_csrf  # ADDED
                                    },
                                    catch_response=True) as response:
                    if response.status_code != 200:
                        response.failure(f"Join room failed: {response.text}")

    # PRESERVED YOUR ORIGINAL play_game METHOD
    @task(5)
    def play_game(self):
        """Simulate puzzle gameplay"""
        if not self.room_id:
            return
            
        # Get CSRF token from room page
        resp = self.client.get(f"/jigsaw/room/{self.room_id}/")
        csrf_token = self._extract_csrf(resp)
        
        if not csrf_token:
            logger.error("Failed to get CSRF token for gameplay")
            return

        # Get pieces
        with self.client.get(f"/jigsaw/get_pieces/?room_id={self.room_id}",
                           catch_response=True) as response:
            if response.status_code != 200:
                response.failure("Failed to get pieces")
                return
                
            try:
                pieces = response.json().get('pieces', [])
            except:
                response.failure("Invalid pieces response")
                return

        # Move random pieces
        for _ in range(random.randint(1, 5)):
            piece = random.choice(pieces)
            with self.client.post("/jigsaw/update_piece_position/",
                                json={
                                    "piece_id": piece['id'],
                                    "new_x": random.randint(0, 800),
                                    "new_y": random.randint(0, 800),
                                    "player_role": "player1"
                                },
                                headers={
                                    "X-CSRFToken": csrf_token,
                                    "Referer": f"{self.host}/jigsaw/room/{self.room_id}/",
                                    "Content-Type": "application/json"
                                },
                                catch_response=True) as response:
                if response.status_code != 200:
                    response.failure(f"Move piece failed: {response.text}")

            # Random chat messages
            if random.random() < 0.3:
                self.send_chat_message(csrf_token)

    # PRESERVED YOUR ORIGINAL view_leaderboard METHOD
    @task(1)
    def view_leaderboard(self):
        """Check the leaderboard"""
        with self.client.get("/jigsaw/leaderboard/",
                           catch_response=True) as response:
            if response.status_code != 200:
                response.failure(f"Leaderboard failed: {response.text}")
            # More flexible content check
            elif not any(x in response.text.lower() for x in ["leaderboard", "ranking"]):
                response.failure("Leaderboard content missing")

    # PRESERVED YOUR ORIGINAL send_chat_message METHOD
    def send_chat_message(self, csrf_token):
        """Helper method to send chat messages"""
        with self.client.post("/jigsaw/send_message/",
                            json={
                                "room_id": self.room_id,
                                "message": f"Test message {random.randint(1, 1000)}"
                            },
                            headers={
                                "X-CSRFToken": csrf_token,
                                "Referer": f"{self.host}/jigsaw/room/{self.room_id}/",
                                "Content-Type": "application/json"
                            },
                            catch_response=True) as response:
            if response.status_code != 200:
                response.failure(f"Send message failed: {response.text}")

# PRESERVED YOUR COMPLETE JigsawPuzzleSequentialUser CLASS
class JigsawPuzzleSequentialUser(HttpUser):
    wait_time = between(1, 3)
    host = "http://localhost:8000"

    def _extract_csrf(self, response):
        match = re.search(r"name=['\"]csrfmiddlewaretoken['\"] value=['\"](.+?)['\"]", response.text)
        return match.group(1) if match else ""

    def generate_test_image(self):
        img = Image.new('RGB', (100, 100), color='red')
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='PNG')
        img_byte_arr.seek(0)
        return img_byte_arr

    def on_start(self):
        self.username = f"seq_user_{random.randint(1, 10000)}"
        self.email = f"{self.username}@example.com"
        self.password = "testpass123"
        self.room_id = None
        
        resp = self.client.get("/user/auth/")
        csrf_token = self._extract_csrf(resp)
        
        with self.client.post("/user/auth/",
                            data={
                                "username": self.username,
                                "email": self.email,
                                "password1": self.password,
                                "password2": self.password,
                                "csrfmiddlewaretoken": csrf_token
                            },
                            headers={"Referer": f"{self.host}/user/auth/"},
                            catch_response=True) as response:
            if response.status_code != 200:
                response.failure(f"Registration failed: {response.text}")

        with self.client.post("/user/auth/",
                            data={
                                "email": self.email,
                                "password": self.password,
                                "csrfmiddlewaretoken": csrf_token
                            },
                            headers={"Referer": f"{self.host}/user/auth/"},
                            catch_response=True) as response:
            if response.status_code != 200:
                response.failure(f"Login failed: {response.text}")

    @task
    class SequentialPuzzleTasks(SequentialTaskSet):
        def _extract_csrf(self, response):
            match = re.search(r"name=['\"]csrfmiddlewaretoken['\"] value=['\"](.+?)['\"]", response.text)
            return match.group(1) if match else ""


        @task
        def create_room(self):
            resp = self.client.get("/jigsaw/create_room/jigsaw/")
            csrf_token = self._extract_csrf(resp)

            test_image = self.parent.generate_test_image()
            room_name = f"Seq Room {random.randint(1, 1000)}"
            difficulty = random.choice(["easy", "medium", "hard"])
            mode = "collaborative"

            data = {
                "name": room_name,
                "difficulty": difficulty,
                "mode": mode,
                "csrfmiddlewaretoken": csrf_token
            }
            files = {
                "puzzle_image": ("test.png", test_image.getvalue(), "image/png")
            }

            with self.client.post("/jigsaw/create_room/jigsaw/",
                    data=data,
                    files=files,
                    headers={
                        "Referer": f"{self.parent.host}/jigsaw/create_room/jigsaw/",
                        "X-CSRFToken": csrf_token
                    },
                    catch_response=True) as response:

                if response.status_code in [200, 302]:
                    if response.status_code == 302:
                        self.parent.room_id = int(response.headers['Location'].split('/')[-2])
                    else:
                        match = re.search(r'room_id:\s*["\'](\d+)["\']', response.text)
                        if match:
                            self.parent.room_id = int(match.group(1))
                        else:
                            response.failure("Could not extract room ID")
                else:
                    response.failure(f"Room creation failed: {response.status_code}")


        @task
        def join_room(self):
            if not self.parent.room_id:
                return
                
            with self.client.get(f"/jigsaw/waiting-room/{self.parent.room_id}/",
                               catch_response=True) as response:
                if response.status_code == 200:
                    match = re.search(r"room_code['\"]?:\s*['\"]([A-Z0-9]{8})['\"]", response.text)
                    if match:
                        room_code = match.group(1)

            if not room_code:
                return

            join_resp = self.client.get("/jigsaw/join_room/")
            join_csrf = self._extract_csrf(join_resp)
            
            with self.client.post("/jigsaw/join_room/",
                                data={
                                    "room_code": room_code,
                                    "csrfmiddlewaretoken": join_csrf
                                },
                                headers={
                                    "Referer": f"{self.parent.host}/jigsaw/join_room/",
                                    "X-CSRFToken": join_csrf  # ADDED
                                },
                                catch_response=True) as response:
                if response.status_code != 200:
                    response.failure(f"Join room failed: {response.text}")

        @task
        def play_puzzle(self):
            if not self.parent.room_id:
                return
                
            resp = self.client.get(f"/jigsaw/room/{self.parent.room_id}/")
            csrf_token = self._extract_csrf(resp)
            
            with self.client.get(f"/jigsaw/get_pieces/?room_id={self.parent.room_id}",
                               catch_response=True) as response:
                if response.status_code != 200:
                    response.failure("Failed to get pieces")
                    return
                    
                try:
                    pieces = response.json().get('pieces', [])
                except:
                    response.failure("Invalid pieces response")
                    return

            for _ in range(10):
                if not pieces:
                    continue
                    
                piece = random.choice(pieces)
                with self.client.post("/jigsaw/update_piece_position/",
                                    json={
                                        "piece_id": piece['id'],
                                        "new_x": random.randint(0, 800),
                                        "new_y": random.randint(0, 800),
                                        "player_role": "player2"
                                    },
                                    headers={
                                        "X-CSRFToken": csrf_token,
                                        "Referer": f"{self.parent.host}/jigsaw/room/{self.parent.room_id}/",
                                        "Content-Type": "application/json"
                                    },
                                    catch_response=True) as response:
                    if response.status_code != 200:
                        response.failure(f"Move piece failed: {response.text}")

        @task
        def stop(self):
            self.interrupt()