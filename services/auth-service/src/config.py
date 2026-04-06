from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "auth-service"
    DEBUG: bool = False
    ALLOWED_ORIGINS: list[str] = ["*"]

    DATABASE_URL: str = "postgresql://cloudoku:cloudoku@postgres:5432/cloudoku"

    JWT_SECRET_KEY: str = "change-me-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRATION_MINUTES: int = 15

    REFRESH_TOKEN_SECRET: str = "change-me-in-production-refresh"
    REFRESH_TOKEN_ALGORITHM: str = "HS256"
    REFRESH_TOKEN_EXPIRATION_DAYS: int = 7

    GITHUB_CLIENT_ID: str = ""
    GITHUB_CLIENT_SECRET: str = ""
    GITHUB_REDIRECT_URI: str = "http://localhost:3000/auth/github/callback"

    class Config:
        env_file = ".env"


settings = Settings()
