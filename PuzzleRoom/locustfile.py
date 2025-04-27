# locustfile.py
from locust import HttpUser, task, between
import random

class PuzzleUser(HttpUser):
    wait_time = between(1, 3)
    
    @task
    def create_room(self):
        # Authenticate
        self.client.post("/login", json={
            "email": "test@example.com",
            "password": "password123"
        })
        
        # Create room
        response = self.client.post("/rooms/create", json={
            "roomName": f"Room-{random.randint(1, 100)}",
            "difficulty": random.choice(["easy", "medium", "hard"])
        })
        room_id = response.json()["room_id"]
        
        # Simulate moves
        for _ in range(5):
            self.client.post(f"/rooms/{room_id}/move", json={
                "piece_id": random.randint(1, 24),
                "row_target": random.randint(0, 4),
                "col_target": random.randint(0, 4)
            })