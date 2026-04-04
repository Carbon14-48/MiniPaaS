import requests
from src.config import settings


def fetch_logs(app_id: int, lines: int = 100) -> list[dict]:
    response = requests.get(
        f"{settings.LOKI_URL}/loki/api/v1/query_range",
        params={
            "query": f'{{app_id="{app_id}"}}',
            "limit": lines,
        },
    )
    response.raise_for_status()
    return response.json().get("data", {}).get("result", [])
