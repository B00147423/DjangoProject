import os
from PIL import Image

PREDEFINED_DIR = os.path.join(os.path.dirname(__file__), 'static', 'jigsaw_puzzle', 'predefined_images')
PIECES_DIR = os.path.join(os.path.dirname(__file__), 'static', 'jigsaw_puzzle', 'predefined_pieces')
GRID_SIZES = {'easy': 4, 'medium': 6, 'hard': 8}

for filename in os.listdir(PREDEFINED_DIR):
    if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
        for difficulty, grid_size in GRID_SIZES.items():
            img = Image.open(os.path.join(PREDEFINED_DIR, filename))
            width, height = img.size
            piece_width = width // grid_size
            piece_height = height // grid_size
            base_name = os.path.splitext(filename)[0]
            out_dir = os.path.join(PIECES_DIR, f"{base_name}_{difficulty}")
            os.makedirs(out_dir, exist_ok=True)
            for i in range(grid_size):
                for j in range(grid_size):
                    box = (j * piece_width, i * piece_height, (j + 1) * piece_width, (i + 1) * piece_height)
                    piece = img.crop(box)
                    piece.save(os.path.join(out_dir, f"{i}_{j}.png"))