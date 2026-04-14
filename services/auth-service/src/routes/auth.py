from fastapi import APIRouter, HTTPException, Depends, Header, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
from typing import Optional
from src.database import get_db
from src.services.auth_service import (
    UserService,
    create_access_token,
    create_refresh_token,
    decode_token,
    get_github_auth_url,
)
from src.models.user import User

router = APIRouter()
security = HTTPBearer(auto_error=False)


class UserRegister(BaseModel):
    email: EmailStr
    password: str
    name: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class GitHubCallback(BaseModel):
    code: str


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: int
    email: str
    name: str
    oauth_provider: Optional[str] = None
    has_password: bool

    class Config:
        from_attributes = True


class GitHubAuthUrlResponse(BaseModel):
    url: str


class GitHubTokenResponse(BaseModel):
    github_token: Optional[str]
    has_github_token: bool


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    if not credentials:
        raise HTTPException(status_code=401, detail="Not authenticated")
    token = credentials.credentials
    payload = decode_token(token, "access")
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")
    user = UserService(db).get_by_id(int(user_id))
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is deactivated")
    return user


@router.post("/register", response_model=TokenResponse)
async def register(user_data: UserRegister, db: Session = Depends(get_db)):
    service = UserService(db)
    user, error = service.register_email(
        email=user_data.email,
        password=user_data.password,
        name=user_data.name,
    )
    if error:
        raise HTTPException(status_code=400, detail=error)
    access_token = create_access_token({"sub": str(user.id)})
    refresh_token = create_refresh_token({"sub": str(user.id)})
    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@router.post("/login", response_model=TokenResponse)
async def login(user_data: UserLogin, db: Session = Depends(get_db)):
    service = UserService(db)
    user, error = service.login_email(email=user_data.email, password=user_data.password)
    if error:
        raise HTTPException(status_code=401, detail=error)
    access_token = create_access_token({"sub": str(user.id)})
    refresh_token = create_refresh_token({"sub": str(user.id)})
    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@router.get("/github", response_model=GitHubAuthUrlResponse)
async def github_auth():
    url = get_github_auth_url()
    return GitHubAuthUrlResponse(url=url)


@router.get("/callback", response_model=TokenResponse)
async def github_callback(code: str = Query(...), db: Session = Depends(get_db)):
    service = UserService(db)
    user, error = await service.login_github(code)
    if error:
        raise HTTPException(status_code=401, detail=error)
    access_token = create_access_token({"sub": str(user.id)})
    refresh_token = create_refresh_token({"sub": str(user.id)})
    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        name=current_user.name,
        oauth_provider=current_user.oauth_provider,
        has_password=current_user.has_password(),
    )


@router.get("/github-token", response_model=GitHubTokenResponse)
async def get_github_token(current_user: User = Depends(get_current_user)):
    return GitHubTokenResponse(
        github_token=current_user.github_access_token,
        has_github_token=current_user.github_access_token is not None,
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(request: RefreshTokenRequest, db: Session = Depends(get_db)):
    payload = decode_token(request.refresh_token, "refresh")
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")
    service = UserService(db)
    user = service.get_by_id(int(user_id))
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is deactivated")
    access_token = create_access_token({"sub": str(user.id)})
    new_refresh_token = create_refresh_token({"sub": str(user.id)})
    return TokenResponse(access_token=access_token, refresh_token=new_refresh_token)
