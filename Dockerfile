# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set the correct working directory
WORKDIR /code

# Install system dependencies
RUN apt-get update && apt-get install -y build-essential cmake libjpeg-dev libpng-dev libtiff-dev libx11-dev libgtk-3-dev

# Copy and install dependencies
COPY requirements.txt /code/
RUN pip install --upgrade pip setuptools wheel
RUN pip install -r requirements.txt

# Copy the entire project into the container
COPY . /code/

# Collect static files
RUN python manage.py collectstatic --noinput --verbosity 3

# Start the application
CMD ["daphne", "-b", "0.0.0.0", "-p", "8000", "PuzzleRoom.asgi:application"]
