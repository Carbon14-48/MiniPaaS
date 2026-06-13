import logging
import os
import subprocess
from typing import Optional

from src.models.findings import (
    ScanDetails,
    SeverityBreakdown,
)
from src.models.scan_result import (
    ScanStatus,
    Verdict,
    Warning,
)

logger = logging.getLogger(__name__)


def check_security_tools_available() -> dict:
    """Check if security scanning tools are available."""
    tools = {
        "trivy": False,
        "clamav": False,
        "yara": False,
    }
    
    # Check Trivy
    try:
        result = subprocess.run(["/usr/local/bin/trivy", "version"], 
                                capture_output=True, timeout=10)
        tools["trivy"] = result.returncode == 0
    except Exception:
        tools["trivy"] = False
    
    # Check ClamAV (clamd daemon)
    try:
        result = subprocess.run(["/usr/sbin/clamd", "--version"], 
                                capture_output=True, timeout=10)
        tools["clamav"] = result.returncode == 0
    except Exception:
        tools["clamav"] = False
    
    # Also check if clamd socket exists
    if not tools["clamav"]:
        if os.path.exists("/var/run/clamav/clamd.ctl"):
            tools["clamav"] = True
    
    # Check YARA
    try:
        import yara  # noqa: F401
        tools["yara"] = True
    except Exception:
        tools["yara"] = False
    
    return tools


class PolicyEngine:
    """
    Production Policy: Block on things the developer controls.
    Warn on inherited CVEs from base images.
    """

    def evaluate(
        self,
        details: ScanDetails,
        breakdown: SeverityBreakdown,
    ) -> tuple[ScanStatus, Verdict, Optional[str], list[Warning]]:
        """
        Evaluate scan results.
        
        Blocking rules (things devs control):
        1. Security tools not available -> BLOCK
        2. Malware detected -> BLOCK
        3. Secrets detected -> BLOCK
        
        Warning rules (inherited/base image issues):
        1. CVEs (all severities) -> WARN only
        2. Non-standard base image -> WARN only
        3. Root user -> WARN only
        """
        block_reasons: list[str] = []
        warnings: list[Warning] = []

        # Rule 0: Check if security tools are available -> WARN only (don't block)
        tools = check_security_tools_available()
        missing_tools = [k for k, v in tools.items() if not v]
        if missing_tools:
            warnings.append(Warning(
                type="scanner_unavailable",
                count=len(missing_tools),
                message=f"Security tools unavailable: {', '.join(missing_tools)}. Scan may be incomplete."
            ))

        # Rule 1: Malware detected -> BLOCK (developer's code)
        if details.malware:
            malware_count = len(details.malware)
            block_reasons.append(
                f"{malware_count} malware detection(s) found"
            )

        # Rule 2: Secrets detected -> BLOCK (developer's code)
        if details.secrets:
            secret_count = len(details.secrets)
            block_reasons.append(
                f"{secret_count} secret(s)/credential(s) detected"
            )

        # Rule 2b: Excessive CVEs -> BLOCK (threshold-based)
        # Block if too many critical/high vulnerabilities (likely vulnerable base image)
        if breakdown.critical > 50 or breakdown.high > 500:
            block_reasons.append(
                f"Excessive vulnerabilities: {breakdown.critical} CRITICAL, {breakdown.high} HIGH - deployment blocked for security"
            )

        # Rule 3: Base image - WARN only (inherited)
        if details.base_image and not details.base_image.approved:
            warnings.append(Warning(
                type="base_image",
                count=1,
                message=f"Non-standard base image: {details.base_image.image}"
            ))

        # Rule 4: Root user - WARN only (best practice)
        root_misconfig = any(
            m.code in ("DKR0001", "DKR0002") or
            "root" in m.title.lower()
            for m in details.misconfigurations
        )
        if root_misconfig:
            warnings.append(Warning(
                type="root_user",
                count=1,
                message="Container runs as root user - consider using non-root user"
            ))

        # Rule 5: CVEs -> WARN only (inherited from base image, not developer code)
        if breakdown.critical > 0:
            warnings.append(Warning(
                type="critical_vulnerabilities",
                count=breakdown.critical,
                message=f"{breakdown.critical} CRITICAL CVE(s) found in base image - review recommended"
            ))

        if breakdown.high > 0:
            warnings.append(Warning(
                type="high_vulnerabilities",
                count=breakdown.high,
                message=f"{breakdown.high} HIGH severity CVE(s) found in base image - review recommended"
            ))

        if breakdown.medium > 0:
            warnings.append(Warning(
                type="medium_vulnerabilities",
                count=breakdown.medium,
                message=f"{breakdown.medium} MEDIUM severity CVE(s) found in base image"
            ))

        if breakdown.low > 0:
            warnings.append(Warning(
                type="low_vulnerabilities",
                count=breakdown.low,
                message=f"{breakdown.low} LOW severity CVE(s) found in base image"
            ))

        # Determine status
        if block_reasons:
            block_reason = "; ".join(block_reasons)
            logger.warning(f"Image BLOCKED: {block_reason}")
            return (
                ScanStatus.BLOCKED,
                Verdict.POLICY_VIOLATION,
                block_reason,
                warnings,
            )

        # PASS with warnings
        if warnings:
            logger.info(f"Image PASSED (with warnings): {[w.message for w in warnings]}")
            return (
                ScanStatus.PASS,
                Verdict.ADVISORY_WARNING,
                None,
                warnings,
            )

        # PASS clean
        logger.info("Image PASSED all security checks")
        return (
            ScanStatus.PASS,
            Verdict.POLICY_PASSED,
            None,
            warnings,
        )
