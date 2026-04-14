import bcrypt
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import Optional
from src.models.user import User
from src.config import settings
import httpx
import jwt
from datetime import datetime, timedelta
import asyncio


async def retry_request(coro_func, max_retries: int = 3, delay: float = 1.0):
    """Retry an async HTTP call with exponential backoff."""
    last_error = None
    for attempt in range(max_retries):
        try:
            return await coro_func()
        except (httpx.ConnectTimeout, httpx.ConnectError, httpx.TimeoutException) as e:
            last_error = e
            if attempt < max_retries - 1:
                await asyncio.sleep(delay * (2 ** attempt))
    raise last_error


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))


def validate_password(password: str) -> tuple[bool, str]:
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    if not any(c.isupper() for c in password):
        return False, "Password must contain at least one uppercase letter"
    if not any(c.islower() for c in password):
        return False, "Password must contain at least one lowercase letter"
    if not any(c.isdigit() for c in password):
        return False, "Password must contain at least one digit"
    return True, ""


def create_access_token(data: dict, expires_minutes: int = None) -> str:
    if expires_minutes is None:
        expires_minutes = settings.JWT_ACCESS_TOKEN_EXPIRATION_MINUTES
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=expires_minutes)
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRATION_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, settings.REFRESH_TOKEN_SECRET, algorithm=settings.REFRESH_TOKEN_ALGORITHM)


def decode_token(token: str, token_type: str = "access") -> Optional[dict]:
    try:
        secret = settings.JWT_SECRET_KEY if token_type == "access" else settings.REFRESH_TOKEN_SECRET
        algorithm = settings.JWT_ALGORITHM if token_type == "access" else settings.REFRESH_TOKEN_ALGORITHM
        payload = jwt.decode(token, secret, algorithms=[algorithm])
        if payload.get("type") != token_type:
            return None
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def get_github_auth_url() -> str:
    params = {
        "client_id": settings.GITHUB_CLIENT_ID,
        "redirect_uri": settings.GITHUB_REDIRECT_URI,
        "scope": "user:email",
    }
    query = "&".join(f"{k}={v}" for k, v in params.items())
    return f"https://github.com/login/oauth/authorize?{query}"


async def exchange_github_code(code: str) -> Optional[dict]:
    async def _do_request():
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "https://github.com/login/oauth/access_token",
                json={
                    "client_id": settings.GITHUB_CLIENT_ID,
                    "client_secret": settings.GITHUB_CLIENT_SECRET,
                    "code": code,
                    "redirect_uri": settings.GITHUB_REDIRECT_URI,
                },
                headers={"Accept": "application/json"},
            )
            if response.status_code != 200:
                return None
            data = response.json()
            if "access_token" not in data:
                return None
            return data
    return await retry_request(_do_request)


async def get_github_user(access_token: str) -> Optional[dict]:
    async def _do_request():
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                "https://api.github.com/user",
                headers={"Authorization": f"Bearer {access_token}", "Accept": "application/json"},
            )
            if response.status_code != 200:
                return None
            return response.json()
    return await retry_request(_do_request)


async def get_github_email(access_token: str) -> Optional[str]:
    async def _do_request():
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                "https://api.github.com/user/emails",
                headers={"Authorization": f"Bearer {access_token}", "Accept": "application/json"},
            )
            if response.status_code != 200:
                return None
            emails = response.json()
            for email_data in emails:
                if email_data.get("primary") and email_data.get("verified"):
                    return email_data.get("email")
            return None
    return await retry_request(_do_request)


class UserService:
    def __init__(self, db: Session):
        self.db = db

    def get_by_email(self, email: str) -> Optional[User]:
        return self.db.query(User).filter(User.email == email.lower()).first()

    def get_by_id(self, user_id: int) -> Optional[User]:
        return self.db.query(User).filter(User.id == user_id).first()

    def get_by_oauth(self, provider: str, oauth_id: str) -> Optional[User]:
        return (
            self.db.query(User)
            .filter(User.oauth_provider == provider, User.oauth_id == oauth_id)
            .first()
        )

    def get_by_github_id(self, github_id: str) -> Optional[User]:
        return self.get_by_oauth("github", github_id)

    def get_github_token(self, user_id: int) -> Optional[str]:
        user = self.get_by_id(user_id)
        if user:
            return user.github_access_token
        return None

    def create(
        self,
        email: str,
        name: str,
        hashed_password: Optional[str] = None,
        oauth_provider: Optional[str] = None,
        oauth_id: Optional[str] = None,
        github_access_token: Optional[str] = None,
    ) -> User:
        user = User(
            email=email.lower(),
            name=name,
            hashed_password=hashed_password,
            oauth_provider=oauth_provider,
            oauth_id=oauth_id,
            github_access_token=github_access_token,
            is_verified=True,
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def register_email(self, email: str, password: str, name: str) -> tuple[Optional[User], Optional[str]]:
        existing = self.get_by_email(email)
        if existing:
            return None, "Email already registered"

        valid, msg = validate_password(password)
        if not valid:
            return None, msg

        hashed = hash_password(password)
        user = self.create(email=email, name=name, hashed_password=hashed)
        return user, None

    def login_email(self, email: str, password: str) -> tuple[Optional[User], Optional[str]]:
        user = self.get_by_email(email)
        if not user:
            return None, "Invalid email or password"
        if not user.has_password():
            return None, "This account uses OAuth login. Please sign in with GitHub."
        if not verify_password(password, user.hashed_password):
            return None, "Invalid email or password"
        if not user.is_active:
            return None, "Account is deactivated"
        return user, None

    async def login_github(self, code: str) -> tuple[Optional[User], Optional[str]]:
        token_data = await exchange_github_code(code)
        if not token_data:
            return None, "Failed to exchange code with GitHub"

        github_user = await get_github_user(token_data["access_token"])
        if not github_user:
            return None, "Failed to get user info from GitHub"

        github_id = str(github_user["id"])
        github_email = await get_github_email(token_data["access_token"]) or github_user.get("email")
        github_name = github_user.get("name") or github_user.get("login") or "GitHub User"

        user = self.get_by_github_id(github_id)
        if user:
            if not user.is_active:
                return None, "Account is deactivated"
            user.github_access_token = token_data["access_token"]
            self.db.commit()
            return user, None

        if not github_email:
            return None, "Could not get email from GitHub. Make sure you have a verified primary email."

        existing_by_email = self.get_by_email(github_email)
        if existing_by_email:
            existing_by_email.oauth_provider = "github"
            existing_by_email.oauth_id = github_id
            existing_by_email.github_access_token = token_data["access_token"]
            self.db.commit()
            return existing_by_email, None

        user = self.create(
            email=github_email,
            name=github_name,
            oauth_provider="github",
            oauth_id=github_id,
            github_access_token=token_data["access_token"],
        )
        return user, None

    def link_github(self, user: User, github_id: str) -> tuple[bool, str]:
        existing = self.get_by_github_id(github_id)
        if existing and existing.id != user.id:
            return False, "This GitHub account is already linked to another user"
        user.oauth_provider = "github"
        user.oauth_id = github_id
        self.db.commit()
        return True, ""
