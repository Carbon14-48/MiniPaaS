"""
db.py
-----
Configure la connexion à PostgreSQL via SQLAlchemy.

SessionLocal : ouvre une session (connexion) à la base pour lire/écrire.
Base         : classe parente de tous les modèles (tables).
get_db()     : fonction FastAPI pour injecter la session dans les routes.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from src.config import settings

# Crée le moteur de connexion à PostgreSQL
engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,   # vérifie que la connexion est vivante avant chaque requête
    pool_size=5,          # 5 connexions simultanées max
    max_overflow=10,      # 10 connexions supplémentaires si besoin
)

# Fabrique de sessions — chaque requête HTTP ouvre et ferme sa propre session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """Classe parente de tous les modèles SQLAlchemy."""
    pass


def get_db():
    """
    Dépendance FastAPI : injectée dans les routes qui ont besoin de la base.
    Ouvre une session, la passe à la route, la ferme proprement après.

    Utilisation dans une route :
        def ma_route(db: Session = Depends(get_db)):
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
