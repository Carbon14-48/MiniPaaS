# Dockerfile du build-service
# Ce fichier sert à containeriser LE BUILD-SERVICE lui-même.
# (différent des Dockerfiles qu'il génère pour les apps utilisateurs)

FROM python:3.11-slim

WORKDIR /app

# Installe git (nécessaire pour gitpython / git clone)
RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

# Copie et installe les dépendances Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copie tout le code source
COPY . .

# Port d'écoute du service
EXPOSE 8002

# Lance le service
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8002"]
