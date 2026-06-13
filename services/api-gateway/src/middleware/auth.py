from fastapi import Request
from fastapi.responses import JSONResponse
import jwt
from src.config import settings


PUBLIC_PATHS = {
    "/", "/health", "/health/", "/docs", "/openapi.json",
    "/auth/register", "/auth/login", "/auth/github", "/auth/callback",
}


async def verify_token(request: Request, call_next):
    path = request.url.path
    if path in PUBLIC_PATHS:
        return await call_next(request)

    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return JSONResponse(status_code=401, content={"detail": "Missing or invalid token"})

    token = auth_header.split(" ")[1]
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        request.state.user = payload
    except jwt.ExpiredSignatureError:
        return JSONResponse(status_code=401, content={"detail": "Token expired"})
    except jwt.InvalidTokenError:
        return JSONResponse(status_code=401, content={"detail": "Invalid token"})

    return await call_next(request)
