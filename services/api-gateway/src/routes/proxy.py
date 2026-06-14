from fastapi import APIRouter, HTTPException, Request, Response
import httpx
from src.config import settings

router = APIRouter()

SERVICE_URLS = {
    "auth": settings.AUTH_SERVICE_URL,
    "repos": settings.DEPLOYER_SERVICE_URL,
    "deployments": settings.DEPLOYER_SERVICE_URL,
    "builds": settings.BUILD_SERVICE_URL,
    "registry": settings.REGISTRY_SERVICE_URL,
    "monitoring": settings.MONITORING_SERVICE_URL,
    "scanner": settings.SECURITY_SCANNER_URL,
}

SERVICE_PATH_PREFIX = {
    "deployments": "/deployments",
    "repos": "/repos",
    "auth": "/auth",
    "builds": "/build",
}


def _build_target_url(service: str, path: str, base_url: str) -> str:
    prefix = SERVICE_PATH_PREFIX.get(service, "")
    if prefix:
        return f"{base_url}{prefix}/{path}" if path else f"{base_url}{prefix}/"
    return f"{base_url}/{path}"


@router.api_route("/{service}/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def proxy(service: str, path: str, request: Request):
    if service not in SERVICE_URLS:
        raise HTTPException(status_code=404, detail=f"Unknown service: {service}")
    
    base_url = SERVICE_URLS[service].rstrip('/')
    target_url = _build_target_url(service, path, base_url)
    
    headers = {k: v for k, v in request.headers.items() if k.lower() not in ("host", "content-length")}
    
    # Builds + scanning can take several minutes
    timeout = 600.0 if service == "builds" else 30.0
    
    try:
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
            body = await request.body()
            response = await client.request(
                method=request.method,
                url=target_url,
                headers=headers,
                content=body if body else None,
                params=request.query_params,
            )
            return Response(
                content=response.content,
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type=response.headers.get("content-type"),
            )
    except httpx.ConnectError:
        raise HTTPException(status_code=503, detail=f"Service {service} unreachable")
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Gateway timeout")