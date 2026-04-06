"""
migrations/env.py
-----------------
Fichier de configuration Alembic.
Indique à Alembic comment se connecter à la base et quels modèles gérer.
Ne pas modifier sauf si tu changes la structure de connexion.
"""

from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
import sys, os

# Permet d'importer les modules src/ depuis ce fichier
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.db import Base
from src.models import job  # noqa — importer pour que les modèles soient connus

config = context.config
fileConfig(config.config_file_name)
target_metadata = Base.metadata


def run_migrations_offline():
    url = config.get_main_option("sqlalchemy.url")
    context.configure(url=url, target_metadata=target_metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
