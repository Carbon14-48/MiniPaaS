import logging
from typing import Optional

from src.config import settings
from src.models.findings import (
    ScanDetails,
    SeverityBreakdown,
    Severity,
)
from src.models.scan_result import (
    ScanStatus,
    Verdict,
    Warning,
)

logger = logging.getLogger(__name__)


class PolicyEngine:
    """
    PERMISSIVE Policy for testing: Only blocks CRITICAL vulnerabilities.
    """

    def evaluate(
        self,
        details: ScanDetails,
        breakdown: SeverityBreakdown,
    ) -> tuple[ScanStatus, Verdict, Optional[str], list[Warning]]:
        """
        Evaluate scan results - PERMISSIVE MODE.
        
        Blocking rules:
        1. Base image not in allowlist -> WARN (not block)
        2. CRITICAL CVE -> BLOCK
        3. Malware detected -> WARN (not block for testing)
        4. Secrets detected -> WARN (not block for testing)
        5. Root user -> WARN (not block for testing)
        
        Warning rules:
        - Everything else becomes a warning only
        """
        block_reasons: list[str] = []
        warnings: list[Warning] = []

        # Rule 1: Base image - WARN only (don't block)
        if details.base_image and not details.base_image.approved:
            warnings.append(Warning(
                type="base_image",
                count=1,
                message=f"Non-standard base image: {details.base_image.image}"
            ))

        # Rule 2: CRITICAL CVEs only - BLOCK
        if breakdown.critical > 0:
            block_reasons.append(
                f"{breakdown.critical} CRITICAL CVE(s) found"
            )

        # Rule 3: Malware - WARN only (not block)
        if details.malware:
            malware_count = len(details.malware)
            warnings.append(Warning(
                type="malware",
                count=malware_count,
                message=f"{malware_count} potential malware detection(s) - review recommended"
            ))

        # Rule 4: Secrets - WARN only (not block)
        if details.secrets:
            secret_count = len(details.secrets)
            warnings.append(Warning(
                type="secrets",
                count=secret_count,
                message=f"{secret_count} potential secret(s) detected - review recommended"
            ))

        # Rule 5: Root user - WARN only (not block)
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

        # Determine status - only block for CRITICAL CVEs
        if block_reasons:
            block_reason = "; ".join(block_reasons)
            logger.warning(f"Image BLOCKED: {block_reason}")
            return (
                ScanStatus.BLOCKED,
                Verdict.POLICY_VIOLATION,
                block_reason,
                warnings,
            )

        # Add CVEs as warnings only (don't block)
        if breakdown.high > 0:
            warnings.append(Warning(
                type="high_vulnerabilities",
                count=breakdown.high,
                message=f"{breakdown.high} HIGH severity CVE(s) found - review recommended"
            ))

        if breakdown.medium > 0:
            warnings.append(Warning(
                type="medium_vulnerabilities",
                count=breakdown.medium,
                message=f"{breakdown.medium} MEDIUM severity CVE(s) found"
            ))

        if breakdown.low > 0:
            warnings.append(Warning(
                type="low_vulnerabilities",
                count=breakdown.low,
                message=f"{breakdown.low} LOW severity CVE(s) found"
            ))

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
