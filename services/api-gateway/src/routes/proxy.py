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


@router.api_route("/{service}/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def proxy(service: str, path: str, request: Request):
    if service not in SERVICE_URLS:
        raise HTTPException(status_code=404, detail=f"Unknown service: {service}")
    
    base_url = SERVICE_URLS[service].rstrip('/')
    # For deployments/repos: need /deployments/path (service name in URL)
    # For builds: use /build (not /builds)
    # For others (monitoring, auth): need /path (no service name)
    if service in ("deployments", "repos"):
        if path:
            target_url = f"{base_url}/{service}/{path}"
        else:
            target_url = f"{base_url}/{service}/"
    elif service == "builds":
        # Build service uses /build endpoint
        if path:
            target_url = f"{base_url}/build/{path}"
        else:
            target_url = f"{base_url}/build/"
    else:
        target_url = f"{base_url}/{path}"
    
    headers = {k: v for k, v in request.headers.items() if k.lower() not in ("host", "content-length")}
    
    try:
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
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
        raise HTTPException(status_code=504, detail=f"Gateway timeout")


@router.api_route("/{service}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def proxy_root(service: str, request: Request):
    if service not in SERVICE_URLS:
        raise HTTPException(status_code=404, detail=f"Unknown service: {service}")
    
    base_url = SERVICE_URLS[service].rstrip('/')
    # For deployments/repos: add service name
    # For builds: use /build
    if service in ("deployments", "repos"):
        target_url = f"{base_url}/{service}/"
    elif service == "builds":
        target_url = f"{base_url}/build/"
    else:
        target_url = base_url
    
    headers = {k: v for k, v in request.headers.items() if k.lower() not in ("host", "content-length")}
    
    try:
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
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
        raise HTTPException(status_code=504, detail=f"Gateway timeout")