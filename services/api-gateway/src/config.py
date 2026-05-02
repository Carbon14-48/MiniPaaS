from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "api-gateway"
    DEBUG: bool = False
    ALLOWED_ORIGINS: list[str] = ["*"]

    # JWT Configuration
    JWT_SECRET_KEY: str = "your-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"

    # Service URLs (localhost for manual dev, or Docker service names)
    AUTH_SERVICE_URL: str = "http://localhost:8001/auth"
    APP_MANAGEMENT_SERVICE_URL: str = "http://localhost:8002"
    BUILD_SERVICE_URL: str = "http://localhost:8003"
    DEPLOYMENT_SERVICE_URL: str = "http://localhost:8004"
    DEPLOYER_SERVICE_URL: str = "http://localhost:8008"
    MONITORING_SERVICE_URL: str = "http://localhost:8006"
    SECURITY_SCANNER_URL: str = "http://localhost:8000"
    REGISTRY_SERVICE_URL: str = "http://localhost:8007"

    class Config:
        env_file = ".env"


settings = Settings()
