# Jigsaw Puzzle Game

A real-time multiplayer puzzle game where players can compete or collaborate to solve puzzles together. Built with Django and WebSockets for real-time interaction.

## What's Inside

- Real-time multiplayer gameplay
- 1v1 competitive mode
- Drag-and-drop puzzle mechanics
- Live score tracking
- User profiles and authentication
- Multiple puzzle types and difficulty levels

## Tech Stack

- Backend: Django + Django Channels
- Frontend: Vanilla JS
- Database: PostgreSQL
- Real-time: WebSockets
- Deployment: Docker + Heroku
- Authentication: Django AllAuth with Google OAuth

## Quick Start

1. Clone the repo:
```bash
git clone https://github.com/B00147423/DjangoProject.git
cd DjangoProject
```

2. Run with Docker:
```bash
docker-compose up --build
```

3. Run migrations:
```bash
docker-compose exec web python manage.py migrate
```

4. Visit http://localhost:8000 and start playing!

## Development

To run the project locally:

```bash
# Start the development server
docker-compose up

# Run tests
docker-compose exec web python manage.py test

# Create a superuser (admin)
docker-compose exec web python manage.py createsuperuser
```

## Features

- **Multiplayer Mode**: Play with friends in real-time
- **Competitive Mode**: Challenge others in 1v1 matches
- **Puzzle Mechanics**: 
  - Drag and drop pieces
  - Automatic piece snapping
  - Piece rotation
  - Win detection
- **User Features**:
  - Google OAuth login
  - User profiles
  - Score tracking
  - Game history

## Contributing

Found a bug or have an idea? Open an issue or submit a pull request!

## Contact

Questions? Reach out at betsunaidzeb@gmail.com

---

Built by beka BVetsunaidze