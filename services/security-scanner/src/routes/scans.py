import tempfile
import time
import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse

from src.models.scan_request import ScanRequest
from src.models.scan_result import ScanResponse, ScanStatus, Verdict, HealthResponse, ToolStatus
from src.models.findings import SeverityBreakdown
from src.scanners import (
    TrivyScanner,
    ClamavScanner,
    YaraScanner,
    TruffleHogScanner,
    DockleScanner,
    check_base_image,
    CosignSigner,
)
from src.services import (
    ResultAggregator,
    PolicyEngine,
    ImageLoader,
    get_image_loader,
)

logger = logging.getLogger(__name__)

router = APIRouter()


def _run_full_scan(image_tag: str, extract_dir: str) -> dict:
    """Run all scanners and return raw results."""
    trivy = TrivyScanner()
    clamav = ClamavScanner()
    yara = YaraScanner()
    trufflehog = TruffleHogScanner()
    dockle = DockleScanner()
    signer = CosignSigner()

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
        with get_image_loader() as loader:
            base_image_str = loader.get_base_image(image_tag)
            base_image_raw = check_base_image(base_image_str)
        logger.info(f"Base image check: {base_image_raw}")
    except Exception as e:
        logger.warning(f"Failed to determine base image: {e}")
        base_image_raw = None

    return {
        "vulnerabilities": trivy_vulns,
        "malware": clamav_findings + yara_findings,
        "secrets": secret_findings,
        "misconfigurations": misconfigs,
        "base_image": base_image_raw,
        "signer": signer,
    }


@router.post("/image", response_model=ScanResponse)
async def scan_image(request: ScanRequest):
    """
    Full image security scan pipeline:
    1. Load image from Docker daemon
    2. Run all scanners (Trivy, ClamAV, YARA, TruffleHog, Dockle)
    3. Aggregate results
    4. Apply policy
    5. Sign if PASS
    """
    start_time = time.time()
    extract_dir = tempfile.mkdtemp(prefix="scan_")

    try:
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

        signed = False
        signature = None
        if status == ScanStatus.PASS:
            try:
                signer: CosignSigner = scan_results["signer"]
                signature = signer.sign(request.image_tag)
                signed = signature is not None
            except Exception as e:
                logger.warning(f"Signing failed (non-fatal): {e}")

        duration = time.time() - start_time

        response = ScanResponse(
            status=status,
            verdict=verdict,
            image_tag=request.image_tag,
            scan_duration_seconds=round(duration, 2),
            severity_breakdown=breakdown,
            block_reason=block_reason,
            policy_passed=status != ScanStatus.BLOCKED,
            signed=signed,
            signature=signature,
            warnings=warnings,
            details=details,
        )

        logger.info(
            f"Scan complete for {request.image_tag}: "
            f"{status.value} in {duration:.1f}s"
        )

        return response

    except FileNotFoundError as e:
        logger.error(f"Image not found: {e}")
        raise HTTPException(status_code=404, detail=str(e))
    except RuntimeError as e:
        logger.error(f"Scan failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected scan error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Scan error: {e}")
    finally:
        import shutil
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

    signer = CosignSigner()
    tools.cosign = "available" if signer.is_available() else "unavailable"

    return tools
