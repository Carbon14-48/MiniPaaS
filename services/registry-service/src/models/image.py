"""
models/image.py
---------------
Table registry_images — une ligne par image pushée.

Chaque push depuis build-service crée une ligne ici.
Le deployment-service lit ces lignes pour savoir quelles images déployer.
"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, BigInteger, DateTime, Boolean
from src.db import Base


class RegistryImage(Base):
    __tablename__ = "registry_images"

    # Identifiant unique dans notre système
    image_id = Column(
        String, primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    # Propriétaire de l'image (user_id vient du build-service)
    user_id = Column(Integer, nullable=False, index=True)

    # Nom de l'application (ex: "myapp")
    app_name = Column(String, nullable=False)

    # Tag original produit par le build-service (ex: "user42/myapp:v1")
    image_tag = Column(String, nullable=False, unique=True)

    # URL complète dans le registry local (ex: "registry:5000/user42/myapp:v1")
    registry_url = Column(String, nullable=False)

    # Empreinte SHA256 retournée par docker push — garantit l'intégrité
    # Format : "sha256:aabbcc112233..."
    digest = Column(String, nullable=True)

    # Taille totale de l'image en bytes
    size_bytes = Column(BigInteger, nullable=True)

    # Date/heure du push réussi
    pushed_at = Column(
        DateTime, nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )

    # Soft delete : False si supprimée, True si active
    # On ne supprime jamais physiquement les lignes — historique conservé
    is_active = Column(Boolean, nullable=False, default=True)
