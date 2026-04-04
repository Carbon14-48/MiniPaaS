# Auth Service

Handles user registration, login, and JWT token management.

## Endpoints

- `POST /auth/register` - Register a new user
- `POST /auth/login` - Login and get JWT token
- `GET /health` - Health check

## Running locally

```bash
pip install -r requirements.txt
uvicorn src.main:app --reload
```
