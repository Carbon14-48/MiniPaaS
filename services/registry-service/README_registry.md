# Registry Service — MiniPaaS

## English Summary

The **Registry Service** is responsible for storing, managing, and exposing Docker images produced by the Build Service. It bridges the build pipeline and the deployment pipeline.

### Key Responsibilities
- Tag Docker images with proper naming conventions
- Push images to the local Docker registry
- Store image metadata in PostgreSQL
- Clean up local Docker daemon images after push
- Provide image information to other services

### Architecture Flow
```
Build Service → Security Scan OK → POST /push → Registry Service → Docker Push → registry:5000
                                                            ↓
                                                     Store metadata in PostgreSQL
                                                            ↓
                                                     Return URL + digest to Build Service
```

### Endpoints
| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/push` | Tag and push image to registry |
| `GET` | `/images/{user_id}` | List user's images |
| `GET` | `/images/tag/{tag}` | Get image by tag |
| `GET` | `/images/{digest}` | Get image by digest |
| `DELETE` | `/images/{digest}` | Soft-delete image |
| `GET` | `/health` | Health check |

---

*For detailed documentation, see below (in French).*

---

Le **Registry Service** est le microservice responsable de stocker, gérer et
exposer les images Docker produites par le Build Service.
Il fait le pont entre le pipeline de build et le pipeline de déploiement.

---

## Sommaire

- [Rôle dans l'architecture](#rôle-dans-larchitecture)
- [Les deux entités à ne pas confondre](#les-deux-entités-à-ne-pas-confondre)
- [Quel registry utiliser et pourquoi](#quel-registry-utiliser-et-pourquoi)
- [Simulation complète de A à Z](#simulation-complète-de-a-à-z)
- [Communication avec les autres services](#communication-avec-les-autres-services)
- [Base de données](#base-de-données)
- [Structure interne du code](#structure-interne-du-code)
- [Prérequis](#prérequis)
- [Installation](#installation)
- [Variables d'environnement](#variables-denvironnement)
- [API Reference](#api-reference)
- [Tests](#tests)
- [Points critiques à ne pas oublier](#points-critiques-à-ne-pas-oublier)

---

## Rôle dans l'architecture

```
build-service:8002
      │
      │  1. Clone repo + docker build + scan CVE
      │  2. Scan OK → POST /push vers registry-service
      ▼
registry-service:8005        ← CE SERVICE
      │
      │  3. docker tag + docker push vers registry local
      │  4. Stocke métadonnées en base PostgreSQL
      │  5. Retourne URL + digest au build-service
      ▼
registry:5000                ← container Docker officiel (stockage physique)
      │
      │  6. Deployment Service fait docker pull depuis ici
      ▼
deployment-service:8004
      │
      │  7. Lance le container de l'utilisateur sur le cluster
```

Le Registry Service est **appelé par le Build Service** après un scan réussi,
et **interrogé par le Deployment Service** avant chaque déploiement.

---

## Les deux entités à ne pas confondre

C'est le point de confusion le plus fréquent. Il y a **deux choses distinctes** :

```
registry:5000
└── Container Docker officiel (image: registry:2)
    Rôle : stockage physique des images sur disque
    Analogue à : un disque dur externe
    Ne contient aucune logique métier
    Expose une API HTTP bas niveau (Docker Registry V2)

registry-service:8005
└── Notre microservice FastAPI
    Rôle : orchestrer les opérations sur le registry
    Analogue à : le manager qui gère le disque dur
    Contient toute la logique : auth, metadata, nettoyage
    Expose une API REST haut niveau pour les autres services
```

**Le build-service n'appelle JAMAIS registry:5000 directement.**
Il appelle uniquement registry-service:8005 qui fait le travail.

---

## Quel registry utiliser et pourquoi

### Docker Registry v2 (image officielle `registry:2`)

C'est le choix retenu. Voici la comparaison complète :

| Option | Coût | Images privées | Complexité | Verdict |
|--------|------|----------------|------------|---------|
| Docker Hub | Gratuit | 1 seule | Faible | Inutilisable pour PaaS |
| AWS ECR | Payant | Illimité | Haute | Pour la production plus tard |
| Harbor | Gratuit | Illimité | Très haute | Trop lourd pour démarrer |
| **registry:2** | **Gratuit** | **Illimité** | **Très faible** | **Choix retenu** |

### Pourquoi registry:2 est le bon choix maintenant

- C'est l'image officielle maintenue par Docker Inc.
- Elle implémente le protocole **Docker Registry HTTP API V2** — le même que Docker Hub.
- Un simple `docker push` ou `docker pull` fonctionne sans modifier quoi que ce soit.
- Elle tourne comme n'importe quel container dans Docker Compose.
- Les images sont stockées dans un volume Docker persistant sur ton serveur.
- Zéro configuration, zéro compte externe, zéro limite.

### Comment registry:2 stocke les images

```
Volume Docker : registry-data
└── /var/lib/registry/
    └── docker/
        └── registry/
            └── v2/
                ├── blobs/          ← couches (layers) de toutes les images
                └── repositories/
                    └── user42/
                        └── myapp/
                            └── tags/
                                └── v1/  ← tag de l'image
```

Chaque image est décomposée en **couches (layers)** partagées entre images.
Si deux images utilisent `FROM python:3.11-slim`, la couche de base n'est stockée qu'une fois.

### Format des URLs dans le registry local

```
registry:5000/{user_id}/{app_name}:{version}

Exemples :
  registry:5000/user42/myapp:v1
  registry:5000/user42/myapp:v2
  registry:5000/user17/api:v1
  registry:5000/user99/frontend:v3
```

Le préfixe `registry:5000` est le nom DNS du container dans le réseau Docker.
Depuis n'importe quel service dans docker-compose, ce nom est résolu automatiquement.

---

## Simulation complète de A à Z

### Scénario : build réussi → push → déploiement

**Étape 1 — Build Service appelle Registry Service**

```http
POST http://registry-service:8005/push
Content-Type: application/json

{
  "image_tag": "user42/myapp:v1",
  "user_id": 42,
  "app_name": "myapp"
}
```

**Étape 2 — Registry Service vérifie que l'image existe localement**

```python
# L'image doit exister sur le daemon Docker (créée par build-service)
client.images.get("user42/myapp:v1")
# Si introuvable → 404 : l'image n'a pas été buildée ou a déjà été nettoyée
```

**Étape 3 — Tag pour le registry local**

```
docker tag user42/myapp:v1  registry:5000/user42/myapp:v1
```

L'image existe maintenant sous deux noms sur le daemon Docker local.

**Étape 4 — Push vers registry:5000**

```
docker push registry:5000/user42/myapp:v1

Output :
  The push refers to repository [registry:5000/user42/myapp]
  abc123def456: Pushed
  sha256abc789: Pushed
  v1: digest: sha256:aabbcc112233... size: 1847
```

Le digest `sha256:aabbcc112233...` est l'empreinte unique de cette image.
Il ne change pas si on push la même image deux fois — idempotent.

**Étape 5 — Nettoyage des images locales**

```
docker rmi user42/myapp:v1
docker rmi registry:5000/user42/myapp:v1
```

L'image est maintenant UNIQUEMENT dans registry:5000, plus sur le daemon local.
Cela libère l'espace disque du serveur de build.

**Étape 6 — Sauvegarde en base PostgreSQL**

```sql
INSERT INTO registry_images (
  image_id, user_id, app_name, image_tag,
  registry_url, digest, size_bytes, pushed_at, is_active
) VALUES (
  'uuid-ici', 42, 'myapp', 'user42/myapp:v1',
  'registry:5000/user42/myapp:v1',
  'sha256:aabbcc112233...', 45678901, NOW(), true
);
```

**Étape 7 — Réponse au Build Service**

```json
{
  "status": "success",
  "image_tag": "user42/myapp:v1",
  "registry_url": "registry:5000/user42/myapp:v1",
  "digest": "sha256:aabbcc112233...",
  "size_bytes": 45678901
}
```

**Étape 8 — Deployment Service interroge les images disponibles**

```http
GET http://registry-service:8005/images/42

Réponse :
[
  {
    "image_id": "uuid-ici",
    "app_name": "myapp",
    "image_tag": "user42/myapp:v1",
    "registry_url": "registry:5000/user42/myapp:v1",
    "digest": "sha256:aabbcc112233...",
    "pushed_at": "2026-04-07T18:00:00Z"
  }
]
```

**Étape 9 — Deployment Service pull et déploie**

```
docker pull registry:5000/user42/myapp:v1
→ L'image est récupérée depuis registry:5000
→ Le Deployer crée un container ou un pod Kubernetes avec cette image
```

---

## Communication avec les autres services

Tous les appels se font via HTTP REST sur le réseau Docker interne.

### Appels reçus par le Registry Service

| Service appelant | Méthode | Endpoint | Corps / Params |
|---|---|---|---|
| build-service | POST | `/push` | `{image_tag, user_id, app_name}` |
| deployment-service | GET | `/images/{user_id}` | — |
| deployment-service | GET | `/images/tag/{image_tag}` | — |
| deployment-service | DELETE | `/images/{image_tag}` | — |
| api-gateway | GET | `/images/me` | Header: Authorization |

### Ce que le Registry Service n'appelle PAS

Le Registry Service est **passif** — il ne fait aucun appel HTTP vers d'autres services.
Il reçoit des demandes, fait ses opérations Docker + base de données, et répond.

Exception : il interagit avec **registry:5000** mais via le **Docker SDK Python**,
pas via HTTP direct. C'est le SDK qui gère la communication avec le daemon Docker.

---

## Base de données

Le registry-service possède **sa propre base PostgreSQL** — principe microservices.
Jamais de base partagée avec build-service ou deployment-service.

### Table `registry_images`

| Colonne | Type | Description |
|---|---|---|
| `image_id` | UUID | Identifiant unique de l'image dans notre système |
| `user_id` | Integer | Propriétaire de l'image |
| `app_name` | String | Nom de l'application (ex: "myapp") |
| `image_tag` | String | Tag original du build (ex: "user42/myapp:v1") |
| `registry_url` | String | URL complète dans le registry local |
| `digest` | String | Empreinte SHA256 de l'image (garantit l'intégrité) |
| `size_bytes` | BigInteger | Taille totale de l'image en bytes |
| `pushed_at` | DateTime | Date/heure du push |
| `is_active` | Boolean | False si supprimée (soft delete) |

### Pourquoi garder les métadonnées en base ?

Le registry:5000 ne stocke que les images binaires — pas de métadonnées riches.
Pour répondre à "liste toutes les images de user42" rapidement, il faut une base SQL.
Interroger le registry:5000 directement pour ça serait lent et complexe.

---

## Structure interne du code

```
services/registry-service/
├── src/
│   ├── main.py                   # Point d'entrée FastAPI
│   ├── config.py                 # Variables d'environnement
│   ├── db.py                     # Connexion PostgreSQL
│   │
│   ├── routes/
│   │   └── registry.py           # Tous les endpoints HTTP
│   │
│   ├── services/
│   │   └── docker_registry.py    # Logique docker tag + push + rmi
│   │
│   └── models/
│       └── image.py              # Modèle SQLAlchemy table registry_images
│
├── tests/
│   ├── test_registry_route.py    # Tests des endpoints
│   └── test_docker_registry.py  # Tests de la logique Docker
│
├── migrations/
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
│
├── Dockerfile
├── requirements.txt
├── alembic.ini
├── .env.example
└── README.md
```

### Rôle de chaque fichier

**`src/services/docker_registry.py`** — le fichier le plus important.
Contient trois fonctions :
- `push_to_registry(image_tag, registry_url)` → tag + push + retourne digest + size
- `delete_from_registry(registry_url)` → supprime une image du registry local
- `image_exists_locally(image_tag)` → vérifie qu'une image existe sur le daemon Docker

**`src/routes/registry.py`** — les endpoints HTTP.
Orchestre : reçoit la requête → appelle docker_registry.py → sauvegarde en base → répond.

**`src/models/image.py`** — la table `registry_images` en SQLAlchemy.

---

## Prérequis

- Python 3.11+ (ou 3.14 avec les versions de dépendances indiquées ci-dessous)
- Docker Engine actif avec socket `/var/run/docker.sock` accessible
- Docker Compose v2+
- PostgreSQL 15+
- Le container `registry:2` doit tourner (géré par docker-compose)
- Le build-service doit avoir pushé une image localement avant d'appeler /push

---

## Installation

### Avec Docker Compose (recommandé)

Depuis la racine du monorepo :

```bash
docker-compose up --build registry-service
```

### Sans Docker (développement direct)

```bash
cd services/registry-service
cp .env.example .env
pip install -r requirements.txt
alembic upgrade head
uvicorn src.main:app --host 0.0.0.0 --port 8005 --reload
```

---

## Variables d'environnement

```env
# URL du registry local Docker (nom du container dans docker-compose)
REGISTRY_URL=http://registry:5000

# Nom du registry pour docker tag (sans http://)
REGISTRY_HOST=registry:5000

# Base de données propre à ce service
DATABASE_URL=postgresql://registryuser:registrypass@registry-db:5432/registrydb

# Environnement
ENV=development
```

---

## API Reference

### `POST /push`

Reçoit une image buildée et la pousse vers le registry local.
Appelé uniquement par le build-service après un scan CVE réussi.

**Body**
```json
{
  "image_tag": "user42/myapp:v1",
  "user_id": 42,
  "app_name": "myapp"
}
```

**Réponse 200**
```json
{
  "status": "success",
  "image_tag": "user42/myapp:v1",
  "registry_url": "registry:5000/user42/myapp:v1",
  "digest": "sha256:aabbcc112233...",
  "size_bytes": 45678901
}
```

**Réponses d'erreur**

| Code | Cas |
|---|---|
| `404` | L'image n'existe pas sur le daemon Docker local |
| `500` | Erreur lors du docker push |
| `503` | Registry:5000 injoignable |

---

### `GET /images/{user_id}`

Liste toutes les images actives d'un utilisateur.
Appelé par le deployment-service avant de déployer.

**Réponse 200**
```json
[
  {
    "image_id": "uuid",
    "app_name": "myapp",
    "image_tag": "user42/myapp:v1",
    "registry_url": "registry:5000/user42/myapp:v1",
    "digest": "sha256:aabbcc...",
    "size_bytes": 45678901,
    "pushed_at": "2026-04-07T18:00:00Z"
  }
]
```

---

### `GET /images/tag/{image_tag}`

Retourne les détails d'une image spécifique par son tag.

**Exemple** : `GET /images/tag/user42%2Fmyapp%3Av1`

---

### `DELETE /images/{image_tag}`

Supprime une image du registry et marque l'entrée en base comme inactive.
Soft delete — l'entrée reste en base avec `is_active=false`.

---

### `GET /health`

Vérifie que le service est opérationnel.

**Réponse**
```json
{
  "status": "ok",
  "service": "registry-service",
  "registry": "registry:5000"
}
```

---

## Tests

```bash
# Tous les tests
pytest tests/ -v

# Avec couverture
pytest tests/ --cov=src --cov-report=term-missing
```

---

## Points critiques à ne pas oublier

### 1. Le socket Docker est obligatoire

```yaml
# dans docker-compose.yml
registry-service:
  volumes:
    - /var/run/docker.sock:/var/run/docker.sock
```

Sans ce montage, `docker.from_env()` plante au démarrage avec une erreur de connexion.

### 2. Le registry doit être en mode insecure

Par défaut Docker refuse de pusher vers un registry HTTP (non HTTPS).
Il faut configurer le daemon Docker de la machine hôte pour accepter `registry:5000`
comme registry non sécurisé en développement local.

Fichier à créer ou modifier sur la machine hôte : `/etc/docker/daemon.json`

```json
{
  "insecure-registries": ["registry:5000", "localhost:5000"]
}
```

Puis redémarrer Docker :
```bash
sudo systemctl restart docker
```

Sans ça, `docker push registry:5000/...` retourne :
```
Get "https://registry:5000/v2/": http: server gave HTTP response to HTTPS client
```

### 3. L'ordre de démarrage dans docker-compose

Le registry-service doit démarrer APRÈS le container `registry:2` (local-registry).
Sinon le premier push échoue car registry:5000 n'est pas encore prêt.

```yaml
registry-service:
  depends_on:
    local-registry:
      condition: service_started
    registry-db:
      condition: service_healthy
```

### 4. Dépendances compatibles Python 3.14

```
fastapi>=0.115.0
uvicorn[standard]>=0.32.0
pydantic>=2.10.0
pydantic-settings>=2.6.0
httpx>=0.28.0
docker>=7.1.0
sqlalchemy>=2.0.36
alembic>=1.14.0
psycopg2-binary>=2.9.10
python-dotenv>=1.0.1
pytest>=8.3.0
pytest-asyncio>=0.24.0
```

Utiliser `>=` et non `==` pour SQLAlchemy et les librairies core —
les versions exactes comme `==2.0.30` ne supportent pas Python 3.14.

### 5. Le digest garantit l'intégrité

Le digest `sha256:...` retourné par docker push est l'empreinte de l'image.
Le Deployment Service DOIT utiliser le digest et non le tag pour déployer en production :

```
# Fragile — le tag peut pointer vers une image différente si on re-push
docker pull registry:5000/user42/myapp:v1

# Robuste — pointe exactement vers cette image précise
docker pull registry:5000/user42/myapp@sha256:aabbcc112233...
```

En développement, le tag suffit. En production, utiliser le digest.

### 6. Nettoyage automatique des images locales

Après chaque push réussi, le registry-service supprime les images du daemon Docker local :

```python
client.images.remove(f"registry:5000/user42/myapp:v1", force=True)
client.images.remove("user42/myapp:v1", force=True)
```

Sans ce nettoyage, le disque du serveur se remplit rapidement.
L'image est safe dans registry:5000 — le daemon local n'en a plus besoin.

### 7. Contrat avec le build-service (existant)

Le build-service appelle déjà `/push` avec ce body exact (voir registry_client.py) :

```json
{
  "image_tag": "user42/myapp:v1",
  "user_id": 42,
  "app_name": "myapp"
}
```

Et attend cette réponse :

```json
{
  "url": "registry:5000/user42/myapp:v1",
  "digest": "sha256:..."
}
```

**Le champ s'appelle `url` dans la réponse** (pas `registry_url`) —
c'est ce que `registry_client.py` du build-service lit avec `response.get("url")`.
Ne pas changer ce nom de champ.

### 8. Contrat avec le deployment-service (à créer)

Le deployment-service devra appeler :

```
GET /images/{user_id}     → pour lister les images disponibles
GET /images/tag/{tag}     → pour les détails avant déploiement
```

Et utiliser le `registry_url` retourné pour faire `docker pull`.
