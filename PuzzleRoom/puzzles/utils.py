#C:\Users\beka\OneDrive\Desktop\Year4DjangoMajor-Project\DjangoProject\PuzzleRoom\puzzles\utils.py
from PIL import Image

def split_image(image_path, rows, cols, scale=1.0):
    img = Image.open(image_path)
    
    # Get original image dimensions
    width, height = img.size
    
    # Scale the entire image
    scaled_width = int(width * scale)
    scaled_height = int(height * scale)
    
    # Use Image.LANCZOS for high-quality downscaling
    img = img.resize((scaled_width, scaled_height), Image.LANCZOS)
    
    # Calculate the new piece dimensions based on the scaled image
    piece_width = scaled_width // cols
    piece_height = scaled_height // rows

    pieces = []
    for row in range(rows):
        for col in range(cols):
            left = col * piece_width
            upper = row * piece_height
            right = (col + 1) * piece_width
            lower = (row + 1) * piece_height
            piece = img.crop((left, upper, right, lower))
            pieces.append(piece)

    # Return the list of pieces
    return pieces



