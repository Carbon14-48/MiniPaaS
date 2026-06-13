from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "api-gateway"
    DEBUG: bool = False
    ALLOWED_ORIGINS: list[str] = ["*"]

    # JWT Configuration
    JWT_SECRET_KEY: str = "your-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"

    # Service URLs (use Docker internal ports)
    AUTH_SERVICE_URL: str = "http://auth-service:8000"
    APP_MANAGEMENT_SERVICE_URL: str = "http://app-management:8000"
    BUILD_SERVICE_URL: str = "http://build-service:8002"
    DEPLOYMENT_SERVICE_URL: str = "http://deployment-service:8000"
    DEPLOYER_SERVICE_URL: str = "http://deployer-service:8000"
    MONITORING_SERVICE_URL: str = "http://monitoring-service:8006"
    SECURITY_SCANNER_URL: str = "http://security-scanner:8000"
    REGISTRY_SERVICE_URL: str = "http://registry-service:8005"

    class Config:
        env_file = ".env"


settings = Settings()
