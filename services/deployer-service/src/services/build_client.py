import httpx
from ..config import settings
from typing import Optional


async def trigger_build(
    token: str,
    repo_url: str,
    branch: str,
    app_name: str
) -> dict:
    async with httpx.AsyncClient(timeout=300.0) as client:
        try:
            response = await client.post(
                f"{settings.BUILD_SERVICE_URL}/build",
                json={
                    "repo_url": repo_url,
                    "branch": branch,
                    "app_name": app_name
                },
                headers={"Authorization": f"Bearer {token}"}
            )
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 400:
                data = response.json()
                detail = data.get("detail", {})
                if isinstance(detail, dict):
                    raise ValueError(detail.get("message", "Build failed"))
                raise ValueError(str(detail))
            else:
                raise RuntimeError(f"Build service error: {response.status_code}")
        except httpx.ConnectError:
            raise RuntimeError("Build service unreachable")
        except Exception as e:
            raise RuntimeError(f"Build trigger failed: {str(e)}")


async def get_build_status(token: str, job_id: str) -> dict:
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.get(
                f"{settings.BUILD_SERVICE_URL}/build/{job_id}",
                headers={"Authorization": f"Bearer {token}"}
            )
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                raise ValueError("Build job not found")
            else:
                raise RuntimeError(f"Build service error: {response.status_code}")
        except httpx.ConnectError:
            raise RuntimeError("Build service unreachable")
        except Exception as e:
            raise RuntimeError(f"Failed to get build status: {str(e)}")


async def get_user_builds(token: str) -> list[dict]:
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.get(
                f"{settings.BUILD_SERVICE_URL}/build/me",
                headers={"Authorization": f"Bearer {token}"}
            )
            if response.status_code == 200:
                return response.json()
            else:
                return []
        except Exception:
            return []
