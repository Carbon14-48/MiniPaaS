from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "deployer-service"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    ENV: str = "development"
    HOST_PORT_RANGE_START: int = 30000
    HOST_PORT_RANGE_END: int = 40000
    
    AUTH_SERVICE_URL: str = "http://auth-service:8000"
    BUILD_SERVICE_URL: str = "http://build-service:8002"
    REGISTRY_SERVICE_URL: str = "http://registry-service:8005"
    
    DATABASE_URL: str = "postgresql://minipaas:minipaas@postgres:5432/minipaas"
    
    GITHUB_API_URL: str = "https://api.github.com"
    
    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
