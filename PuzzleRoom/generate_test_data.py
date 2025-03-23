import os
import django
import random
from django.utils import timezone

# Set the Django settings module correctly
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'PuzzleRoom.settings')
django.setup()

from jigsaw_puzzle.models import JigsawPuzzleRoom, User

def generate_test_data():
    difficulties = ["easy", "medium", "hard"]
    modes = ["versus", "collaborative"]
    
    users = list(User.objects.all())
    if len(users) < 2:
        print("⚠️ Not enough users to assign to rooms. Create more users first.")
        return

    test_data = []

    for difficulty in difficulties:
        for mode in modes:
            for i in range(100):
                player1 = random.choice(users)
                player2 = random.choice(users)
                
                while player2 == player1:
                    player2 = random.choice(users)

                completion_time = random.randint(60, 600)
                moves_taken = random.randint(30, 200)
                created_at = timezone.now() - timezone.timedelta(days=random.randint(1, 365))

                room = JigsawPuzzleRoom.objects.create(
                    name=f"Test Room {i+1} {difficulty} {mode}",
                    difficulty=difficulty,
                    mode=mode,
                    completed=True,
                    completion_time=completion_time,
                    moves_taken=moves_taken,
                    player1=player1,
                    player2=player2,
                    created_at=created_at
                )
                test_data.append(room)

    print(f"✅ Successfully created {len(test_data)} test rooms!")

# Run the function
generate_test_data()
