import httpx
from ..config import settings


async def get_image_by_tag(image_tag: str) -> dict:
    encoded_tag = image_tag.replace("/", "%2F").replace(":", "%3A")
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.get(
                f"{settings.REGISTRY_SERVICE_URL}/images/tag/{encoded_tag}"
            )
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                raise ValueError(f"Image {image_tag} not found in registry")
            else:
                raise RuntimeError(f"Registry service error: {response.status_code}")
        except httpx.ConnectError:
            raise RuntimeError("Registry service unreachable")
        except Exception as e:
            raise RuntimeError(f"Failed to get image: {str(e)}")


async def list_user_images(user_id: int) -> list[dict]:
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.get(
                f"{settings.REGISTRY_SERVICE_URL}/images/{user_id}"
            )
            if response.status_code == 200:
                return response.json()
            else:
                return []
        except Exception:
            return []
