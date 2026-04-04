from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "auth-service"
    DEBUG: bool = False
    ALLOWED_ORIGINS: list[str] = ["*"]

    DATABASE_URL: str = "postgresql://cloudoku:cloudoku@postgres:5432/cloudoku"

    JWT_SECRET_KEY: str = "change-me-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_MINUTES: int = 60

    class Config:
        env_file = ".env"


settings = Settings()
