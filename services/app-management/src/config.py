from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "app-management"
    DEBUG: bool = False
    ALLOWED_ORIGINS: list[str] = ["*"]

    DATABASE_URL: str = "postgresql://cloudoku:cloudoku@postgres:5432/cloudoku"

    BUILD_SERVICE_URL: str = "http://build-service:8003"
    DEPLOYMENT_SERVICE_URL: str = "http://deployment-service:8004"

    class Config:
        env_file = ".env"


settings = Settings()
