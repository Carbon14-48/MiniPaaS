# Dockerfile du build-service
# Ce fichier sert à containeriser LE BUILD-SERVICE lui-même.
# (différent des Dockerfiles qu'il génère pour les apps utilisateurs)

# checkov:skip=CKV_DOCKER_3:requires root for Docker socket access
FROM python:3.11-slim

WORKDIR /app

# Installe git (nécessaire pour gitpython / git clone)
# hadolint ignore=DL3008
RUN apt-get update && apt-get install -y --no-install-recommends git && rm -rf /var/lib/apt/lists/*

# Copie et installe les dépendances Python
COPY requirements.txt .
RUN pip install --no-cache-dir --only-binary :all: -r requirements.txt

# Copie tout le code source
COPY . .

# Port d'écoute du service
EXPOSE 8002

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD python -c "import socket;s=socket.socket();s.connect(('localhost',8002));s.close()" || exit 1

# Lance le service
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8002"]
