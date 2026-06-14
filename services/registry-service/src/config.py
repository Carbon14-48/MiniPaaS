from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    registry_host: str = "localhost:5000"
    registry_url: str = "http://localhost:5000"
    database_url: str = "postgresql://minipaas:minipaas@postgres:5432/minipaas"  # NOSONAR
    env: str = "development"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
