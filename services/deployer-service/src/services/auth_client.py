import httpx
from ..config import settings


async def verify_token(token: str) -> int:
    async with httpx.AsyncClient(timeout=5.0) as client:
        try:
            response = await client.get(
                f"{settings.AUTH_SERVICE_URL}/auth/me",
                headers={"Authorization": f"Bearer {token}"}
            )
            if response.status_code == 200:
                data = response.json()
                return data.get("id")
            elif response.status_code in [401, 403]:
                raise ValueError("Token invalide ou expire")
            else:
                raise RuntimeError(f"Auth service error: {response.status_code}")
        except httpx.ConnectError:
            raise RuntimeError("Auth service unreachable")
        except Exception as e:
            raise RuntimeError(f"Auth verification failed: {str(e)}")


async def get_user_info(token: str) -> dict:
    async with httpx.AsyncClient(timeout=5.0) as client:
        try:
            response = await client.get(
                f"{settings.AUTH_SERVICE_URL}/auth/me",
                headers={"Authorization": f"Bearer {token}"}
            )
            if response.status_code == 200:
                return response.json()
            else:
                raise ValueError(f"Failed to get user info: {response.status_code}")
        except httpx.ConnectError:
            raise RuntimeError("Auth service unreachable")
        except Exception as e:
            raise RuntimeError(f"Failed to get user info: {str(e)}")
