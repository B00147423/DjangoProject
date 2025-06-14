# Dockerfile for Django project with Daphne and ASGI support
# Use the official Python image as a base image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DJANGO_SETTINGS_MODULE=PuzzleRoom.settings

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    cmake \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY PuzzleRoom/requirements.txt .

# Create a filtered requirements file without Windows-specific packages
RUN grep -v "pywin32\|pypiwin32" requirements.txt > requirements_filtered.txt

# Install Python dependencies in stages
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir urllib3 && \
    pip install --no-cache-dir -r requirements_filtered.txt

# Copy project files
COPY PuzzleRoom/ .

# Create a non-root user
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

# Run migrations and start the server
CMD python manage.py migrate && daphne -b 0.0.0.0 -p 8000 PuzzleRoom.asgi:application
