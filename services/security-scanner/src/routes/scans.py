import os
import tarfile
import tempfile
import time
import logging
import shutil
from typing import Optional

from fastapi import APIRouter, HTTPException
import docker

from src.models.scan_request import ScanRequest
from src.models.scan_result import ScanResponse, ScanStatus, Verdict, ToolStatus
from src.models.findings import SeverityBreakdown
from src.scanners import (
    TrivyScanner,
    ClamavScanner,
    YaraScanner,
    TruffleHogScanner,
    DockleScanner,
    check_base_image,
)
from src.services import ResultAggregator, PolicyEngine
from src.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()


def _extract_image(image_tag: str, dest_dir: str) -> bool:
    """
    Extract the merged filesystem of a Docker image to a directory.
    Uses docker create + docker cp to get the actual files visible at runtime,
    not raw layer tarballs. This is what TruffleHog, ClamAV, and YARA need
    to scan actual application files and secrets.
    """
    client = docker.from_env()
    container = None
    try:
        container = client.containers.create(image_tag)
        bits, _ = container.get_archive("/")
        tar_path = os.path.join(dest_dir, "rootfs.tar")
        with open(tar_path, "wb") as f:
            for chunk in bits:
                f.write(chunk)
        with tarfile.open(tar_path, "r") as tar:
            tar.extractall(dest_dir)
        os.remove(tar_path)
        logger.info(f"Extracted {image_tag} filesystem to {dest_dir}")
        return True
    except Exception as e:
        logger.warning(f"Failed to extract image {image_tag}: {e}")
        return False
    finally:
        if container:
            try:
                container.remove(force=True)
            except Exception:
                pass
        try:
            client.close()
        except Exception:
            pass


def _run_full_scan(image_tag: str, extract_dir: str) -> dict:
    """Run all scanners and return raw results."""
    trivy = TrivyScanner()
    clamav = ClamavScanner()
    yara = YaraScanner()
    trufflehog = TruffleHogScanner()
    dockle = DockleScanner()

    logger.info(f"Starting full security scan for {image_tag}")

    trivy_vulns = trivy.scan(image_tag)
    logger.info(f"Trivy: found {len(trivy_vulns)} vulnerabilities")

    clamav_findings = clamav.scan(image_tag, extract_dir)
    logger.info(f"ClamAV: found {len(clamav_findings)} malware detections")

    yara_findings = yara.scan(extract_dir)
    logger.info(f"YARA: found {len(yara_findings)} YARA rule matches")

    secret_findings = trufflehog.scan(extract_dir)
    logger.info(f"TruffleHog: found {len(secret_findings)} secrets")

    misconfigs = dockle.scan(image_tag)
    logger.info(f"Dockle: found {len(misconfigs)} misconfigurations")

    base_image_raw = None
    try:
        client = docker.from_env()
        try:
            image_info = client.api.inspect_image(image_tag)
            
            base_str = None
            
            img_tags = image_info.get("RepoTags", [])
            if img_tags:
                base_str = img_tags[0]
            
            if not base_str:
                parent_id = image_info.get("Parent", "")
                if not parent_id:
                    base_str = image_tag
                else:
                    try:
                        parent_image = client.api.inspect_image(parent_id)
                        parent_tags = parent_image.get("RepoTags", [])
                        if parent_tags:
                            base_str = parent_tags[0]
                        else:
                            grandparent_id = parent_image.get("Parent", "")
                            if grandparent_id:
                                grandparent_image = client.api.inspect_image(grandparent_id)
                                grandparent_tags = grandparent_image.get("RepoTags", [])
                                if grandparent_tags:
                                    base_str = grandparent_tags[0]
                    except Exception:
                        base_str = image_tag
            
            if not base_str:
                base_str = image_tag
            
            base_image_raw = check_base_image(base_str)
        finally:
            client.close()
        logger.info(f"Base image check: {base_image_raw}")
    except Exception as e:
        logger.warning(f"Failed to determine base image: {e}")
        base_image_raw = check_base_image(image_tag)

    return {
        "vulnerabilities": trivy_vulns,
        "malware": clamav_findings + yara_findings,
        "secrets": secret_findings,
        "misconfigurations": misconfigs,
        "base_image": base_image_raw,
    }


@router.post("/image", response_model=ScanResponse)
async def scan_image(request: ScanRequest):
    """
    Full image security scan pipeline:
    1. Extract image layers
    2. Run all scanners (Trivy, ClamAV, YARA, TruffleHog, Dockle)
    3. Aggregate results
    4. Apply policy
    """
    start_time = time.time()
    extract_dir = tempfile.mkdtemp(prefix="scan_")

    try:
        _extract_image(request.image_tag, extract_dir)

        scan_results = _run_full_scan(request.image_tag, extract_dir)

        aggregator = ResultAggregator()
        details, breakdown = aggregator.aggregate(
            vulnerabilities=scan_results["vulnerabilities"],
            malware=scan_results["malware"],
            secrets=scan_results["secrets"],
            misconfigurations=scan_results["misconfigurations"],
            base_image=scan_results["base_image"],
        )

        policy = PolicyEngine()
        status, verdict, block_reason, warnings = policy.evaluate(
            details=details,
            breakdown=breakdown,
        )

        duration = time.time() - start_time

        response = ScanResponse(
            status=status,
            verdict=verdict,
            image_tag=request.image_tag,
            scan_duration_seconds=round(duration, 2),
            severity_breakdown=breakdown,
            block_reason=block_reason,
            policy_passed=status != ScanStatus.BLOCKED,
            warnings=warnings,
            details=details,
        )

        logger.info(
            f"Scan complete for {request.image_tag}: "
            f"{status.value} in {duration:.1f}s"
        )

        return response

    except docker.errors.NotFound:
        logger.error(f"Image not found: {request.image_tag}")
        raise HTTPException(status_code=404, detail=f"Image not found: {request.image_tag}")
    except RuntimeError as e:
        logger.error(f"Scan failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected scan error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Scan error: {e}")
    finally:
        try:
            shutil.rmtree(extract_dir)
        except Exception:
            pass


@router.get("/health/tools")
async def health_tools():
    """Check availability of all scanning tools."""
    tools = ToolStatus()

    trivy = TrivyScanner()
    try:
        import subprocess
        result = subprocess.run(
            [trivy.trivy_path, "version"],
            capture_output=True, text=True, timeout=10,
        )
        tools.trivy = "available" if result.returncode == 0 else "error"
    except Exception:
        tools.trivy = "unavailable"

    clamav = ClamavScanner()
    tools.clamav = "available" if clamav.is_available() else "unavailable"

    yara_scanner = YaraScanner()
    tools.yara = "available" if yara_scanner.is_available() else "unavailable"

    trufflehog = TruffleHogScanner()
    tools.trufflehog = "available" if trufflehog.is_available() else "unavailable"

    return tools
