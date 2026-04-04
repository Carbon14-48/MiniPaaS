import requests
from src.config import settings


def fetch_metrics(app_id: int) -> dict:
    response = requests.get(
        f"{settings.PROMETHEUS_URL}/api/v1/query",
        params={"query": f'container_cpu_usage_seconds_total{{app_id="{app_id}"}}'},
    )
    response.raise_for_status()
    return response.json().get("data", {})
