"""
db.py
-----
Connexion SQLAlchemy à PostgreSQL.
Identique en structure aux autres services (build-service, registry-service).
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from src.config import settings

engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    """Dépendance FastAPI — injectée dans les routes."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
