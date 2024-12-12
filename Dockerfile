# Use the official Python image
FROM python:3.11

# Set the working directory
WORKDIR /app

# Copy only the relevant folder (PuzzleRoom) into the container
COPY DjangoProject/PuzzleRoom /app

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Set environment variables
ENV DJANGO_SETTINGS_MODULE=PuzzleRoom.settings

# Run migrations and start Daphne
CMD python manage.py migrate && daphne -b 0.0.0.0 -p 8000 PuzzleRoom.asgi:application
