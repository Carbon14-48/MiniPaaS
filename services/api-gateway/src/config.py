from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "api-gateway"
    DEBUG: bool = False
    ALLOWED_ORIGINS: list[str] = ["*"]

    # JWT Configuration
    JWT_SECRET_KEY: str = "your-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"

    # Service URLs (internal Docker - using IPs for now)
    AUTH_SERVICE_URL: str = "http://172.18.0.9:8000/auth"
    APP_MANAGEMENT_SERVICE_URL: str = "http://172.18.0.5:8000"
    BUILD_SERVICE_URL: str = "http://172.18.0.6:8002"
    DEPLOYMENT_SERVICE_URL: str = "http://172.18.0.11:8000"
    DEPLOYER_SERVICE_URL: str = "http://172.18.0.10:8000"
    MONITORING_SERVICE_URL: str = "http://172.18.0.7:8006"
    SECURITY_SCANNER_URL: str = "http://172.18.0.14:8000"
    REGISTRY_SERVICE_URL: str = "http://172.18.0.8:8005"

    class Config:
        env_file = ".env"


settings = Settings()
