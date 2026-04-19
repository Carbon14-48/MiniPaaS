# Monitoring Service — MiniPaaS

Le **Monitoring Service** collecte et expose les métriques et logs des applications
déployées par les utilisateurs. Il s'intègre dans l'architecture MiniPaaS de façon
**entièrement passive** — il ne modifie rien dans les autres services.

---

## Sommaire

- [Principe fondamental](#principe-fondamental)
- [Ce que ce service fait concrètement](#ce-que-ce-service-fait-concrètement)
- [Architecture de monitoring](#architecture-de-monitoring)
- [Comment il trouve les containers à monitorer](#comment-il-trouve-les-containers-à-monitorer)
- [Métriques collectées](#métriques-collectées)
- [Prometheus et Grafana](#prometheus-et-grafana)
- [API Reference](#api-reference)
- [Base de données](#base-de-données)
- [Structure du code](#structure-du-code)
- [Installation](#installation)
- [Variables d'environnement](#variables-denvironnement)
- [Tests](#tests)
- [Intégration docker-compose](#intégration-docker-compose)

---

## Principe fondamental

**Ce service ne casse RIEN dans l'architecture existante.**

Il est entièrement passif :

```
auth-service    ──┐
build-service   ──┤
registry-service──┤──► (aucune interaction) ──► monitoring-service
scanner-service ──┤                              observe en lecture seule
deployer-service──┘                              via Docker daemon
```

Les autres services **n'ont pas besoin de connaître** le monitoring-service.
Il n'appelle aucun endpoint des autres services.
Il ne s'insère dans aucun pipeline existant.
Il peut être ajouté ou retiré sans impacter les autres.

---

## Ce que ce service fait concrètement

### Collecte automatique (toutes les 30 secondes)

Un scheduler APScheduler tourne en arrière-plan et exécute automatiquement :

```
Toutes les 30s :
  1. Trouve tous les containers "utilisateurs" via Docker SDK
  2. Pour chaque container : lit CPU%, RAM, réseau
  3. Sauvegarde en base PostgreSQL (table container_metrics)

Toutes les heures :
  Supprime les métriques plus vieilles que 7 jours (nettoyage automatique)
```

### Ce qu'on peut lire ensuite

```
GET /metrics/myapp           → historique CPU/RAM des 60 dernières minutes
GET /logs/myapp              → logs applicatifs depuis la base
GET /logs/myapp/live         → logs en direct depuis Docker (sans base)
GET /health/myapp            → est-ce que le container tourne ?
GET /metrics                 → toutes les métriques au format Prometheus
                               → Prometheus scrape ça toutes les 15s
                               → Grafana affiche les graphiques
```

---

## Architecture de monitoring

```
┌─────────────────────────────────────────────────────────────────┐
│                      RÉSEAU DOCKER minipaas-net                  │
│                                                                  │
│  Containers utilisateurs (déployés par deployer-service)         │
│  minipaas_42_myapp   minipaas_17_api   minipaas_99_frontend      │
│         │                   │                   │                │
│         └───────────────────┴───────────────────┘               │
│                             │  Docker SDK (lecture stats/logs)   │
│                             ▼                                    │
│                  monitoring-service:8006                         │
│                  ┌─────────────────────┐                        │
│                  │  APScheduler        │                        │
│                  │  (collecte 30s)     │                        │
│                  │  FastAPI            │                        │
│                  │  Routes REST        │                        │
│                  └──────────┬──────────┘                        │
│                             │                                    │
│              ┌──────────────┴──────────────┐                    │
│              ▼                             ▼                    │
│        monitor-db:5432              /metrics endpoint           │
│        (PostgreSQL)                 (format Prometheus)         │
│                                           │                     │
└───────────────────────────────────────────┼─────────────────────┘
                                            │ scrape toutes les 15s
                                            ▼
                                     prometheus:9090
                                            │
                                            ▼
                                      grafana:3000
                                   (dashboards visuels)
```

---

## Comment il trouve les containers à monitorer

Le monitoring-service utilise une **double stratégie** pour trouver
les containers des utilisateurs — compatible avec l'état actuel
du deployer-service ET avec son évolution future.

### Stratégie 1 — Labels Docker (propre, future)

Si le deployer-service ajoute des labels aux containers :

```python
# Dans deployer-service, lors du docker run :
container = client.containers.run(
    image,
    labels={
        "minipaas": "true",
        "minipaas.app_id": "myapp",
        "minipaas.user_id": "42",
    }
)
```

Le monitoring les trouve avec `filters={"label": "minipaas=true"}`.

### Stratégie 2 — Convention de nommage (actuelle)

Si les containers sont nommés selon la convention :
```
minipaas_{user_id}_{app_name}
```

Exemple : `minipaas_42_myapp` → user_id=42, app_id=myapp

Le monitoring parcourt tous les containers running et filtre
ceux dont le nom commence par `minipaas_`.

**Les deux stratégies coexistent** — pas de conflit.
Les services internes MiniPaaS (`build-service`, `auth-service`, etc.)
ne sont jamais inclus car leur nom ne commence pas par `minipaas_`
et ils n'ont pas le label `minipaas=true`.

---

## Métriques collectées

### Par container, toutes les 30 secondes

| Métrique | Type | Description |
|---|---|---|
| `cpu_percent` | Float | % CPU utilisé (0-100 par CPU) |
| `memory_usage_bytes` | BigInt | RAM utilisée en bytes |
| `memory_limit_bytes` | BigInt | RAM limite du container |
| `memory_percent` | Float | % RAM utilisée (0-100) |
| `network_rx_bytes` | BigInt | Total bytes reçus |
| `network_tx_bytes` | BigInt | Total bytes envoyés |
| `status` | String | running / exited / paused |

### Calcul du CPU

Docker retourne des **compteurs cumulatifs** — pas un pourcentage direct.
La formule utilisée :

```
cpu_delta    = cpu_stats.total - precpu_stats.total
system_delta = cpu_stats.system - precpu_stats.system
cpu_percent  = (cpu_delta / system_delta) × num_cpus × 100
```

`docker.stats(stream=False)` fait deux snapshots automatiquement
pour calculer le delta — c'est le comportement normal de Docker.

---

## Prometheus et Grafana

### Les trois composants distincts

```
monitoring-service (NOTRE CODE)
  → collecte les données
  → expose GET /metrics au format texte Prometheus

prometheus:9090 (CONTAINER OFFICIEL — aucun code)
  → lit GET /metrics toutes les 15s
  → stocke les séries temporelles
  → configuration : prometheus.yml (fourni dans ce repo)

grafana:3000 (CONTAINER OFFICIEL — aucun code)
  → lit Prometheus
  → affiche les dashboards
  → dashboard MiniPaaS fourni dans grafana/dashboards/minipaas.json
```

### Format Prometheus exposé par GET /metrics

```
# HELP minipaas_container_cpu_percent CPU usage percent
# TYPE minipaas_container_cpu_percent gauge
minipaas_container_cpu_percent{app_id="myapp",user_id="42",container="minipaas_42_myapp"} 23.5
minipaas_container_cpu_percent{app_id="api",user_id="17",container="minipaas_17_api"} 5.1

# HELP minipaas_container_memory_percent Memory usage percent
# TYPE minipaas_container_memory_percent gauge
minipaas_container_memory_percent{app_id="myapp",user_id="42",container="minipaas_42_myapp"} 45.2
```

### Fichiers de configuration fournis

```
monitoring-service/
├── prometheus.yml                              ← config scraping Prometheus
└── grafana/
    ├── provisioning/
    │   ├── datasources/prometheus.yml          ← branche auto Prometheus → Grafana
    │   └── dashboards/dashboard.yml            ← charge auto le dashboard
    └── dashboards/
        └── minipaas.json                       ← dashboard CPU/RAM/réseau
```

Ces fichiers sont montés dans docker-compose — Grafana se configure tout seul.

---

## API Reference

### Métriques

#### `GET /metrics/{app_id}`
Métriques d'une app sur les N dernières minutes.

**Query params :** `minutes` (défaut 60)

**Réponse**
```json
[
  {
    "app_id": "myapp",
    "user_id": 42,
    "container_name": "minipaas_42_myapp",
    "cpu_percent": 23.5,
    "memory_usage_bytes": 134217728,
    "memory_percent": 45.2,
    "network_rx_bytes": 1024000,
    "network_tx_bytes": 512000,
    "status": "running",
    "collected_at": "2026-04-19T10:00:00Z"
  }
]
```

#### `GET /metrics/user/{user_id}`
Toutes les métriques des apps d'un utilisateur.

#### `GET /metrics/summary`
Dernière valeur connue par app — vue d'ensemble.

#### `GET /metrics`
Format texte Prometheus — scrapé par Prometheus.

---

### Logs

#### `GET /logs/{app_id}`
Logs depuis la base PostgreSQL.

**Query params :** `minutes` (défaut 60), `level` (INFO/WARN/ERROR/DEBUG), `limit` (défaut 200)

#### `GET /logs/{app_id}/live`
Logs **en direct** depuis le Docker daemon sans passer par la base.
Utile juste après un déploiement.

**Query params :** `tail` (défaut 100, max 500)

#### `GET /logs/user/{user_id}`
Logs récents de toutes les apps d'un utilisateur.

#### `POST /logs/{app_id}/collect`
Force une collecte immédiate des logs — sans attendre le scheduler.

---

### Health

#### `GET /health`
Healthcheck du service lui-même (base de données + Docker daemon).

```json
{
  "status": "ok",
  "service": "monitoring-service",
  "port": 8006,
  "database": "ok",
  "docker_daemon": "ok"
}
```

#### `GET /health/{app_id}`
Santé d'une application spécifique — combine statut live + dernières métriques.

```json
{
  "app_id": "myapp",
  "status": "running",
  "healthy": true,
  "container_name": "minipaas_42_myapp",
  "last_cpu_percent": 23.5,
  "last_memory_percent": 45.2
}
```

#### `GET /health/containers/all`
État de tous les containers monitorés en temps réel.

---

## Base de données

Base PostgreSQL **propre** au monitoring-service.
Jamais partagée avec les autres services.

### Table `container_metrics`

| Colonne | Type | Description |
|---|---|---|
| `id` | UUID (PK) | Identifiant unique de la mesure |
| `app_id` | String | Nom de l'app (ex: myapp) |
| `user_id` | Integer | Propriétaire |
| `container_name` | String | Nom Docker du container |
| `container_id` | String | ID court Docker |
| `cpu_percent` | Float | % CPU |
| `memory_usage_bytes` | BigInt | RAM utilisée |
| `memory_limit_bytes` | BigInt | RAM limite |
| `memory_percent` | Float | % RAM |
| `network_rx_bytes` | BigInt | Bytes reçus |
| `network_tx_bytes` | BigInt | Bytes envoyés |
| `status` | String | Statut Docker |
| `collected_at` | DateTime | Horodatage de la mesure |

### Table `log_entries`

| Colonne | Type | Description |
|---|---|---|
| `id` | UUID (PK) | Identifiant unique |
| `app_id` | String | App source |
| `user_id` | Integer | Propriétaire |
| `container_id` | String | Container source |
| `container_name` | String | Nom Docker |
| `level` | String | INFO / WARN / ERROR / DEBUG |
| `message` | Text | Contenu du log |
| `log_timestamp` | DateTime | Timestamp issu du container |
| `collected_at` | DateTime | Quand on l'a stocké |

### Rétention automatique

Les métriques et logs plus vieux que `METRICS_RETENTION_DAYS` jours
(défaut 7) sont supprimés automatiquement par un job horaire.
Pas de croissance infinie de la base.

---

## Structure du code

```
services/monitoring-service/
│
├── src/
│   ├── main.py                       # FastAPI + lifespan scheduler
│   ├── config.py                     # Variables d'environnement
│   ├── db.py                         # Connexion PostgreSQL SQLAlchemy
│   │
│   ├── models/
│   │   ├── metric.py                 # Table container_metrics
│   │   └── log_entry.py              # Table log_entries
│   │
│   ├── routes/
│   │   ├── metrics.py                # GET /metrics/*
│   │   ├── logs.py                   # GET /logs/*
│   │   └── health.py                 # GET /health/*
│   │
│   └── services/
│       ├── docker_collector.py       # Stats CPU/RAM/réseau via Docker SDK
│       ├── log_collector.py          # Logs containers + détection niveau
│       └── scheduler.py              # APScheduler collecte 30s + nettoyage 1h
│
├── tests/
│   ├── test_metrics_route.py         # 6 tests endpoints métriques
│   └── test_docker_collector.py      # 11 tests logique collecte
│
├── migrations/                       # Alembic
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
│
├── prometheus.yml                    # Config scraping Prometheus
├── grafana/
│   ├── provisioning/
│   │   ├── datasources/prometheus.yml
│   │   └── dashboards/dashboard.yml
│   └── dashboards/minipaas.json      # Dashboard prêt à utiliser
│
├── Dockerfile
├── requirements.txt
├── alembic.ini
├── .env.example
└── README.md
```

---

## Installation

### Sans Docker (développement direct)

```bash
cd services/monitoring-service
python3.11 -m venv venv
source venv/bin/activate
cp .env.example .env
# Éditer .env : remplacer monitor-db par localhost
pip install -r requirements.txt
uvicorn src.main:app --host 0.0.0.0 --port 8006 --reload
```

### Tests

```bash
pytest tests/ -v
pytest tests/ --cov=src --cov-report=term-missing
```

---

## Variables d'environnement

| Variable | Défaut | Description |
|---|---|---|
| `DATABASE_URL` | `postgresql://...@monitor-db:5432/monitordb` | PostgreSQL |
| `COLLECT_INTERVAL_SECONDS` | `30` | Fréquence collecte métriques |
| `METRICS_RETENTION_DAYS` | `7` | Rétention données en jours |
| `LOG_TAIL_LINES` | `100` | Lignes logs par défaut |
| `ENV` | `development` | development / production |

En développement local (sans Docker Compose), remplacer `monitor-db` par `localhost` dans `DATABASE_URL`.

---

## Intégration docker-compose

À ajouter dans le `docker-compose.yml` racine quand tu seras prêt.
Ces blocs sont **indépendants** — leur ajout ne casse rien d'existant.

```yaml
# ── Monitoring Service ────────────────────────────────────────────
monitoring-service:
  build: ./services/monitoring-service
  ports:
    - "8006:8006"
  environment:
    - DATABASE_URL=postgresql://monitoruser:monitorpass@monitor-db:5432/monitordb
    - COLLECT_INTERVAL_SECONDS=30
    - METRICS_RETENTION_DAYS=7
    - ENV=development
  volumes:
    - /var/run/docker.sock:/var/run/docker.sock
  depends_on:
    monitor-db:
      condition: service_healthy
  networks:
    - minipaas-net

# ── Base de données du monitoring ─────────────────────────────────
monitor-db:
  image: postgres:15-alpine
  environment:
    POSTGRES_USER: monitoruser
    POSTGRES_PASSWORD: monitorpass
    POSTGRES_DB: monitordb
  volumes:
    - monitor-db-data:/var/lib/postgresql/data
  healthcheck:
    test: ["CMD-SHELL", "pg_isready -U monitoruser -d monitordb"]
    interval: 5s
    timeout: 5s
    retries: 5
  networks:
    - minipaas-net

# ── Prometheus ────────────────────────────────────────────────────
prometheus:
  image: prom/prometheus:latest
  ports:
    - "9090:9090"
  volumes:
    - ./services/monitoring-service/prometheus.yml:/etc/prometheus/prometheus.yml
  depends_on:
    - monitoring-service
  networks:
    - minipaas-net

# ── Grafana ───────────────────────────────────────────────────────
grafana:
  image: grafana/grafana:latest
  ports:
    - "3000:3000"
  environment:
    - GF_SECURITY_ADMIN_PASSWORD=minipaas
    - GF_USERS_ALLOW_SIGN_UP=false
  volumes:
    - ./services/monitoring-service/grafana/provisioning:/etc/grafana/provisioning
    - ./services/monitoring-service/grafana/dashboards:/etc/grafana/provisioning/dashboards
    - grafana-data:/var/lib/grafana
  depends_on:
    - prometheus
  networks:
    - minipaas-net

# ── Volumes à ajouter dans la section volumes: ────────────────────
# monitor-db-data:
# grafana-data:
```

### Accès une fois lancé

| Service | URL | Description |
|---|---|---|
| monitoring-service | http://localhost:8006 | API REST |
| monitoring-service | http://localhost:8006/docs | Swagger UI |
| Prometheus | http://localhost:9090 | Interface Prometheus |
| Grafana | http://localhost:3000 | Dashboards (admin/minipaas) |

---

## Ce que le deployer-service peut faire pour améliorer le monitoring

Pour une identification parfaite des containers, le deployer-service
peut ajouter ces labels lors du `docker run` ou `docker create` :

```python
labels = {
    "minipaas": "true",
    "minipaas.app_id": app_name,
    "minipaas.user_id": str(user_id),
}
```

Sans ces labels, le monitoring fonctionne quand même via la convention
de nommage `minipaas_{user_id}_{app_name}` — aucune modification
n'est obligatoire dans le deployer-service.
