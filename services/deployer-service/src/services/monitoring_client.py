import httpx
from ..config import settings


async def cleanup_app_metrics(token: str, app_name: str) -> tuple[int, int]:
    async with httpx.AsyncClient(timeout=10.0) as client:
        headers = {"Authorization": f"Bearer {token}"}
        deleted_metrics = 0
        deleted_logs = 0

        try:
            r = await client.delete(
                f"{settings.MONITORING_SERVICE_URL}/metrics/{app_name}",
                headers=headers
            )
            if r.status_code == 200:
                data = r.json()
                deleted_metrics = data.get("deleted_metrics", 0)
        except Exception:
            pass

        try:
            r = await client.delete(
                f"{settings.MONITORING_SERVICE_URL}/logs/{app_name}",
                headers=headers
            )
            if r.status_code == 200:
                data = r.json()
                deleted_logs = data.get("deleted_logs", 0)
        except Exception:
            pass

        return deleted_metrics, deleted_logs
