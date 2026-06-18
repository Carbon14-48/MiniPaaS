import logging
import os
import subprocess
from typing import Optional

from src.config import settings

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
        result = subprocess.run([settings.TRIVY_PATH, "version"], 
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
    Policy engine that uses BLOCK_ON_* settings from config.
    Block: malware, secrets, critical CVEs, root user (configurable).
    Warn: high/medium/low CVEs, base image issues.
    """

    def evaluate(
        self,
        details: ScanDetails,
        breakdown: SeverityBreakdown,
    ) -> tuple[ScanStatus, Verdict, Optional[str], list[Warning]]:
        block_reasons: list[str] = []
        warnings: list[Warning] = []

        # Check if security tools are available
        tools = check_security_tools_available()
        missing_tools = [k for k, v in tools.items() if not v]
        if missing_tools:
            warnings.append(Warning(
                type="scanner_unavailable",
                count=len(missing_tools),
                message=f"Security tools unavailable: {', '.join(missing_tools)}. Scan may be incomplete."
            ))

        # Malware detected -> BLOCK
        if settings.BLOCK_ON_MALWARE and details.malware:
            malware_count = len(details.malware)
            block_reasons.append(f"{malware_count} malware detection(s) found")

        # Secrets detected -> BLOCK
        if settings.BLOCK_ON_SECRETS and details.secrets:
            secret_count = len(details.secrets)
            block_reasons.append(f"{secret_count} secret(s)/credential(s) detected")

        # Critical/High CVEs -> BLOCK if above thresholds
        if settings.BLOCK_ON_HIGH_CVES:
            crit = breakdown.critical
            high = breakdown.high
            if crit > 50 or high > 500:
                parts = []
                if crit > 50:
                    parts.append(f"{crit} critical")
                if high > 500:
                    parts.append(f"{high} high")
                block_reasons.append(
                    f"Excessive vulnerabilities: {', '.join(parts)} CVE(s) found"
                )

        # Root user -> BLOCK (configurable)
        if settings.BLOCK_ON_ROOT_USER:
            root_misconfig = any(
                m.code in ("DKR0001", "DKR0002") or
                "root" in m.title.lower()
                for m in details.misconfigurations
            )
            if root_misconfig:
                block_reasons.append("Container runs as root user")

        # High CVEs -> WARN
        if breakdown.high > 0:
            warnings.append(Warning(
                type="high_vulnerabilities",
                count=breakdown.high,
                message=f"{breakdown.high} HIGH severity CVE(s) found"
            ))

        # Medium CVEs -> WARN
        if breakdown.medium > 0:
            warnings.append(Warning(
                type="medium_vulnerabilities",
                count=breakdown.medium,
                message=f"{breakdown.medium} MEDIUM severity CVE(s) found"
            ))

        # Low CVEs -> WARN
        if breakdown.low > 0:
            warnings.append(Warning(
                type="low_vulnerabilities",
                count=breakdown.low,
                message=f"{breakdown.low} LOW severity CVE(s) found"
            ))

        # Non-standard base image -> WARN
        if details.base_image and not details.base_image.approved:
            warnings.append(Warning(
                type="base_image",
                count=1,
                message=f"Non-standard base image: {details.base_image.image}"
            ))

        if block_reasons:
            block_reason = "; ".join(block_reasons)
            logger.warning(f"Image BLOCKED: {block_reason}")
            return (
                ScanStatus.BLOCKED,
                Verdict.POLICY_VIOLATION,
                block_reason,
                warnings,
            )

        if warnings:
            logger.info(f"Image PASSED (with warnings): {[w.message for w in warnings]}")
            return (
                ScanStatus.PASS,
                Verdict.ADVISORY_WARNING,
                None,
                warnings,
            )

        logger.info("Image PASSED all security checks")
        return (
            ScanStatus.PASS,
            Verdict.POLICY_PASSED,
            None,
            warnings,
        )
