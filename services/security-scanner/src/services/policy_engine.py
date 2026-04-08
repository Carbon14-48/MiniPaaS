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
    Applies the MiniPaaS blocking policy to aggregated scan results.
    Determines whether an image passes, warns, or is blocked.
    """

    def evaluate(
        self,
        details: ScanDetails,
        breakdown: SeverityBreakdown,
    ) -> tuple[ScanStatus, Verdict, Optional[str], list[Warning]]:
        """
        Evaluate scan results against the policy.
        Returns (status, verdict, block_reason, warnings).

        Blocking rules (in priority order):
        1. Base image not in allowlist -> BLOCK
        2. Any CRITICAL CVE -> BLOCK
        3. Any HIGH CVE (if BLOCK_ON_HIGH_CVES=True) -> BLOCK
        4. Any malware detected -> BLOCK
        5. Any secret detected -> BLOCK
        6. USER directive missing (root user) -> BLOCK

        Warning rules:
        1. MEDIUM CVEs only -> WARN
        2. LOW CVEs only -> WARN
        3. Non-critical misconfigurations -> WARN
        """
        block_reasons: list[str] = []
        warnings: list[Warning] = []

        # Rule 1: Base image
        if details.base_image and not details.base_image.approved:
            reason = f"Unapproved base image: {details.base_image.image}"
            if details.base_image.suggestion:
                reason += f" — {details.base_image.suggestion}"
            block_reasons.append(reason)

        # Rule 2: CRITICAL CVEs
        if breakdown.critical > 0:
            block_reasons.append(
                f"{breakdown.critical} CRITICAL CVE(s) found"
            )

        # Rule 3: HIGH CVEs
        if settings.BLOCK_ON_HIGH_CVES and breakdown.high > 0:
            block_reasons.append(
                f"{breakdown.high} HIGH CVE(s) found"
            )

        # Rule 4: Malware
        if settings.BLOCK_ON_MALWARE and details.malware:
            malware_count = len(details.malware)
            block_reasons.append(
                f"{malware_count} malware detection(s)"
            )

        # Rule 5: Secrets
        if settings.BLOCK_ON_SECRETS and details.secrets:
            secret_count = len(details.secrets)
            block_reasons.append(
                f"{secret_count} secret(s) detected in image"
            )

        # Rule 6: Root user misconfiguration
        if settings.BLOCK_ON_ROOT_USER:
            root_misconfig = any(
                m.code in ("DKR0001", "DKR0002") or
                "root" in m.title.lower()
                for m in details.misconfigurations
            )
            if root_misconfig:
                block_reasons.append("Container runs as root user (USER directive missing)")

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

        # Check warnings
        if breakdown.medium > 0:
            warnings.append(Warning(
                type="medium_vulnerabilities",
                count=breakdown.medium,
                message=f"{breakdown.medium} MEDIUM severity CVE(s) found — "
                        "deployment allowed but review recommended"
            ))

        if breakdown.low > 0:
            warnings.append(Warning(
                type="low_vulnerabilities",
                count=breakdown.low,
                message=f"{breakdown.low} LOW severity CVE(s) found"
            ))

        non_critical_misconfigs = [
            m for m in details.misconfigurations
            if m.severity not in (Severity.CRITICAL, Severity.HIGH)
        ]
        if non_critical_misconfigs:
            warnings.append(Warning(
                type="misconfigurations",
                count=len(non_critical_misconfigs),
                message=f"{len(non_critical_misconfigs)} non-critical "
                        "configuration warnings"
            ))

        if warnings:
            logger.info(
                f"Image WARN: {[w.message for w in warnings]}"
            )
            return (
                ScanStatus.WARN,
                Verdict.ADVISORY_WARNING,
                None,
                warnings,
            )

        # PASS
        logger.info("Image PASSED all security policy checks")
        return (
            ScanStatus.PASS,
            Verdict.POLICY_PASSED,
            None,
            warnings,
        )
