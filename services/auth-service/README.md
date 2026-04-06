# Auth Service

Handles user registration, login, JWT token management, and GitHub OAuth.

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/auth/register` | Register with email + password |
| `POST` | `/auth/login` | Login with email + password |
| `GET` | `/auth/github` | Get GitHub OAuth URL |
| `POST` | `/auth/github/callback` | Exchange GitHub code for tokens |
| `GET` | `/auth/me` | Get current user (requires JWT) |
| `POST` | `/auth/refresh` | Refresh access token |
| `GET` | `/health` | Health check |

## Auth Flow

### Email/Password

1. **Register**: `POST /auth/register` with `{email, password, name}`
2. **Login**: `POST /auth/login` with `{email, password}`
3. Returns `{access_token, refresh_token, token_type}`

### GitHub OAuth (Frontend Redirect Flow)

1. Frontend calls `GET /auth/github` to get the GitHub OAuth URL
2. Redirect user to that URL
3. GitHub redirects to your `GITHUB_REDIRECT_URI` with `?code=...`
4. Frontend calls `POST /auth/github/callback` with `{code: "..."}`
5. Returns `{access_token, refresh_token, token_type}`

### Protected Endpoints

Include JWT in header: `Authorization: Bearer <access_token>`

### Token Refresh

Use refresh token to get new access token:
```
POST /auth/refresh
{"refresh_token": "..."}
```

## Environment Variables

```env
# Database
DATABASE_URL=postgresql://cloudoku:cloudoku@postgres:5432/cloudoku

# JWT
JWT_SECRET_KEY=your-secret-key
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRATION_MINUTES=15

REFRESH_TOKEN_SECRET=your-refresh-secret
REFRESH_TOKEN_ALGORITHM=HS256
REFRESH_TOKEN_EXPIRATION_DAYS=7

# GitHub OAuth
GITHUB_CLIENT_ID=your-github-client-id
GITHUB_CLIENT_SECRET=your-github-client-secret
GITHUB_REDIRECT_URI=http://localhost:3000/auth/github/callback
```

## Running Locally

```bash
pip install -r requirements.txt

# Run migrations
alembic upgrade head

# Start server
uvicorn src.main:app --reload --port 8001
```

## Running Tests

```bash
pytest tests/ -v
```

## Docker

```bash
docker build -t cloudoku-auth-service .
docker run -p 8001:8000 --env-file .env cloudoku-auth-service
```
