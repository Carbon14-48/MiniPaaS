import logging
from typing import Optional

from src.models.findings import (
    Vulnerability,
    Secret,
    MalwareFinding,
    Misconfiguration,
    BaseImageCheck,
    ScanDetails,
    SeverityBreakdown,
    Severity,
)

logger = logging.getLogger(__name__)


class ResultAggregator:
    """Merges results from all scanners into a single ScanDetails object."""

    def aggregate(
        self,
        vulnerabilities: list[Vulnerability],
        malware: list[MalwareFinding],
        secrets: list[Secret],
        misconfigurations: list[Misconfiguration],
        base_image: Optional[BaseImageCheck],
    ) -> tuple[ScanDetails, SeverityBreakdown]:
        """
        Aggregate all scanner results into a ScanDetails and SeverityBreakdown.
        Returns both the full details and a summary of severity counts.
        """
        details = ScanDetails(
            vulnerabilities=sorted(
                vulnerabilities,
                key=lambda v: (
                    self._severity_order(v.severity),
                    v.id
                )
            ),
            malware=malware,
            secrets=secrets,
            misconfigurations=sorted(
                misconfigurations,
                key=lambda m: self._severity_order(m.severity)
            ),
            base_image=base_image,
        )

        breakdown = self._compute_breakdown(vulnerabilities, misconfigurations)

        return details, breakdown

    def _compute_breakdown(
        self,
        vulnerabilities: list[Vulnerability],
        misconfigurations: list[Misconfiguration],
    ) -> SeverityBreakdown:
        """Compute CVE severity breakdown from vulnerability list."""
        breakdown = SeverityBreakdown()

        for vuln in vulnerabilities:
            severity_str = (
                vuln.severity.value
                if hasattr(vuln.severity, "value")
                else str(vuln.severity)
            ).upper()
            if severity_str == "CRITICAL":
                breakdown.critical += 1
            elif severity_str == "HIGH":
                breakdown.high += 1
            elif severity_str == "MEDIUM":
                breakdown.medium += 1
            elif severity_str == "LOW":
                breakdown.low += 1

        return breakdown

    def _severity_order(self, severity) -> int:
        """Return numeric priority for sorting (lower = more severe)."""
        val = severity.value if hasattr(severity, "value") else str(severity)
        order = {
            "CRITICAL": 0,
            "HIGH": 1,
            "MEDIUM": 2,
            "LOW": 3,
            "UNKNOWN": 4,
        }
        return order.get(val.upper(), 99)
