from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, EmailStr
from datetime import datetime, timedelta
import jwt
from src.config import settings

router = APIRouter()


class UserRegister(BaseModel):
    email: EmailStr
    password: str
    name: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str


def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=settings.JWT_EXPIRATION_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


@router.post("/register", response_model=TokenResponse)
async def register(user: UserRegister):
    return {
        "access_token": create_access_token({"sub": user.email, "name": user.name}),
        "token_type": "bearer",
    }


@router.post("/login", response_model=TokenResponse)
async def login(user: UserLogin):
    return {
        "access_token": create_access_token({"sub": user.email}),
        "token_type": "bearer",
    }
