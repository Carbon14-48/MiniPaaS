"""
services/scanner_client.py
--------------------------
Calls security-scanner:8006 after a successful docker build.
If the scanner blocks the image (policy violation), the build is aborted.
If the scanner warns, the build proceeds but warnings are logged.

New response format (v2.0):
  {
    "status": "PASS" | "WARN" | "BLOCKED",
    "verdict": "policy_violation | policy_passed | advisory_warning",
    "severity_breakdown": {"critical": N, "high": N, "medium": N, "low": N},
    "block_reason": "...",
    "policy_passed": bool,
    "signed": bool,
    "warnings": [...],
    "details": {...}
  }
"""

import httpx
from fastapi import HTTPException, status
from src.config import settings


async def scan_image(image_tag: str, user_id: int, app_name: str) -> dict:
    """
    Sends the image to security-scanner for full security analysis.

    Params:
        image_tag: tag of the image to scan (e.g. "user42/myapp:v1")
        user_id: owner user ID
        app_name: application name

    Returns:
        Full scan result dict from security-scanner.

    Raises:
        HTTPException 503: scanner unreachable (fail-safe — blocks build)
        HTTPException 400: image blocked by policy
    """
    try:
        async with httpx.AsyncClient(timeout=300.0) as client:
            response = await client.post(
                f"{settings.scanner_service_url}/scans/image",
                json={
                    "image_tag": image_tag,
                    "user_id": user_id,
                    "app_name": app_name,
                }
            )
            response.raise_for_status()
    except httpx.ConnectError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Security scanner unreachable — build blocked for safety"
        )
    except httpx.HTTPStatusError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Security scanner error: {e.response.text}"
        )

    result = response.json()

    if result.get("status") == "BLOCKED":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "message": f"Security policy violation: {result.get('block_reason')}",
                "status": "BLOCKED",
                "severity_breakdown": result.get("severity_breakdown"),
                "details": result.get("details"),
            }
        )

    return result
