# Dockerfile for Django project with Daphne and ASGI support
# Use the official Python image as a base image
FROM python:3.11

WORKDIR /app

COPY DjangoProject/PuzzleRoom /app


RUN pip install --no-cache-dir -r requirements.txt


ENV DJANGO_SETTINGS_MODULE=PuzzleRoom.settings


CMD python manage.py migrate && daphne -b 0.0.0.0 -p 8000 PuzzleRoom.asgi:application
