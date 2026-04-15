# Monitoring Service

> **Status:** 🔧 STUB - NOT YET IMPLEMENTED
> **Note:** Container logs are currently accessible via Docker CLI. This service is planned for centralized logging and metrics collection.

## Purpose

The Monitoring Service is designed to provide:
- Centralized log aggregation
- Real-time log streaming
- Metrics collection and visualization
- Alerting and notifications
- Performance monitoring
- Health monitoring

## Planned Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/logs/{app_id}` | Get application logs |
| `GET` | `/logs/{app_id}/stream` | Stream logs (Server-Sent Events) |
| `GET` | `/logs/search` | Search logs across apps |
| `GET` | `/metrics/{app_id}` | Get application metrics |
| `GET` | `/metrics` | Get all metrics |
| `GET` | `/metrics/summary` | Get metrics summary |
| `GET` | `/health/{app_id}` | Get application health |
| `GET` | `/alerts` | List active alerts |
| `POST` | `/alerts` | Create alert rule |
| `GET` | `/health` | Health check |

## Metrics to Collect

### Container Metrics
- CPU usage (percentage)
- Memory usage (bytes)
- Network I/O
- Disk I/O

### Application Metrics
- Request count
- Response time (p50, p90, p99)
- Error rate
- Active connections

### System Metrics
- Container count
- Image storage used
- Network packets

## Data Model (Planned)

```python
class LogEntry:
    id: str
    app_id: str
    container_id: str
    timestamp: datetime
    level: str  # INFO, WARN, ERROR
    message: str
    metadata: dict

class Metric:
    id: str
    app_id: str
    metric_type: str  # cpu, memory, requests
    value: float
    unit: str
    timestamp: datetime

class Alert:
    id: str
    app_id: str
    condition: str
    threshold: float
    severity: str  # LOW, MEDIUM, HIGH, CRITICAL
    enabled: bool
    created_at: datetime
```

## Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  Deployer   │────►│   Docker    │────►│ Prometheus  │
│  Service    │     │   Daemon    │     │   (metrics)│
└─────────────┘     └─────────────┘     └──────┬──────┘
                                                 │
                                                 ▼
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  Client     │◄────│ Monitoring  │◄────│  Grafana    │
│  Dashboard  │     │  Service    │     │  (UI)      │
└─────────────┘     │   (8005)   │     └─────────────┘
                    └──────┬──────┘
                           │
                           ▼
                    ┌─────────────┐
                    │    Loki     │
                    │   (logs)   │
                    └─────────────┘
```

## Log Aggregation

### Sources
- Container stdout/stderr
- Application logs
- System logs
- Access logs

### Log Pipeline
```
Container ──► Fluentd/Fluent Bit ──► Loki ──► Grafana
```

### Log Search
- Full-text search
- Filter by level, app, time range
- Regular expression support
- Export to file

## Metrics Visualization

### Grafana Dashboards
- Container resource usage
- Application performance
- Request latency histograms
- Error rate trends

### Alerts
- CPU > 80% for 5 minutes
- Memory > 90% for 5 minutes
- Error rate > 5%
- Response time > 2s

## Running Locally

```bash
cd services/monitoring-service
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Start Prometheus and Loki (via Docker)
docker run -d -p 9090:9090 prom/prometheus
docker run -d -p 3100:3100 grafana/loki

uvicorn src.main:app --reload --port 8005
```

## Future Enhancements

- [ ] Prometheus integration
- [ ] Loki integration for logs
- [ ] Grafana dashboard provisioning
- [ ] Real-time log streaming (WebSocket/SSE)
- [ ] Alert rule engine
- [ ] Email/Slack notifications
- [ ] Metric aggregation
- [ ] Performance baselining

## Related Documentation

- [Main README](../../README.md)
- [Deployer Service](../deployer-service/README.md)
- [Prometheus](https://prometheus.io/docs/)
- [Grafana](https://grafana.com/docs/)
- [Loki](https://grafana.com/docs/loki/)
