# Auth Service

MiniPaaS auth microservice for:
- Email/password authentication
- GitHub OAuth login
- JWT access + refresh token issuance
- Current-user introspection (`/auth/me`)
- GitHub OAuth token retrieval for service-to-service communication

## Current Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/auth/register` | Register with email/password/name |
| `POST` | `/auth/login` | Login with email/password |
| `GET` | `/auth/github` | Generate GitHub OAuth authorize URL |
| `GET` | `/auth/callback?code=...` | Exchange GitHub OAuth code for tokens |
| `GET` | `/auth/me` | Get current user from access token |
| `GET` | `/auth/github-token` | Get stored GitHub OAuth token (for service-to-service) |
| `POST` | `/auth/refresh` | Rotate/refresh access + refresh tokens |
| `GET` | `/health/` | Health check |

## Auth Flows

### 1) Email + Password

1. Call `POST /auth/register` to create account.
2. Call `POST /auth/login` to sign in.
3. Response includes:
   - `access_token`
   - `refresh_token`
   - `token_type` (`bearer`)

### 2) GitHub OAuth (Frontend Redirect)

1. Frontend calls `GET /auth/github`.
2. Frontend redirects user to returned GitHub URL.
3. GitHub redirects to `GITHUB_REDIRECT_URI` with `?code=...`.
4. Frontend calls `GET /auth/callback?code=...`.
5. Service returns bearer tokens.

### 3) GitHub Token for Service-to-Service

Other services (like deployer-service) need the GitHub OAuth token to access repositories:

```http
GET /auth/github-token
Authorization: Bearer <access_token>
```

Response:
```json
{
  "github_token": "gho_xxxxxxxxxxxx"
}
```

This endpoint is used by the deployer-service to:
- List user's GitHub repositories
- Get repository branches
- Clone repositories for building

### 4) Protected Route

Use access token in header:

```http
Authorization: Bearer <access_token>
```

### 5) Refresh Tokens

Send refresh token to rotate both tokens:

```json
POST /auth/refresh
{
  "refresh_token": "..."
}
```

## Data Model (users table)

- `id` (int, PK)
- `email` (unique)
- `name`
- `hashed_password` (nullable for OAuth-only users)
- `is_active`
- `is_verified`
- `oauth_provider` (nullable, e.g. `github`)
- `oauth_id` (nullable)
- `created_at`
- `updated_at`

## Environment Variables

```env
# Database
DATABASE_URL=postgresql://minipaas:minipaas@localhost:5432/minipaas

# JWT Access Token
JWT_SECRET_KEY=CHANGE_ME_generate_with_openssl_rand_base64_32
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRATION_MINUTES=15

# Refresh Token
REFRESH_TOKEN_SECRET=CHANGE_ME_generate_with_openssl_rand_base64_32
REFRESH_TOKEN_ALGORITHM=HS256
REFRESH_TOKEN_EXPIRATION_DAYS=7

# GitHub OAuth
GITHUB_CLIENT_ID=CHANGE_ME
GITHUB_CLIENT_SECRET=CHANGE_ME
GITHUB_REDIRECT_URI=http://localhost:5173/oauth/github/callback

# CORS
ALLOWED_ORIGINS=["http://localhost:5173"]
```

Generate secure secrets:

```bash
openssl rand -base64 32
```

## Local Run

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Create/update schema
alembic upgrade head

# Start API
uvicorn src.main:app --reload --port 8001
```

## Quick API Test

```bash
# Register
curl -X POST http://localhost:8001/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@minipaas.com","password":"TestPass123","name":"Test User"}'

# Login
curl -X POST http://localhost:8001/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@minipaas.com","password":"TestPass123"}'

# GitHub authorize URL
curl http://localhost:8001/auth/github

# Token refresh
curl -X POST http://localhost:8001/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{"refresh_token":"<your-refresh-token>"}'
```

## Frontend Test App

There is a React + TypeScript + Bun test client in `frontend/` that exercises register/login/OAuth/me/refresh.

- Frontend: `http://localhost:5173`
- Auth API: `http://localhost:8001`

## Troubleshooting

- `redirect_uri is not associated with this application`
  - Update your GitHub OAuth app callback URL to exactly:
    `http://localhost:5173/oauth/github/callback`
- OAuth callback returns `401` intermittently on first attempt
  - Retry once; this can happen during transient code exchange timing.
- Arch Linux pip `externally-managed-environment`
  - Use a virtual environment (`python -m venv venv`).

## Tests

```bash
pytest tests/ -v
```
