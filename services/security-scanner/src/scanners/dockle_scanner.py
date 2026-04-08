import json
import subprocess
import tempfile
import os
import logging

from src.config import settings
from src.models.findings import Misconfiguration, Severity

logger = logging.getLogger(__name__)


class DockleScanner:
    """CIS Docker benchmark scanner using Dockle."""

    DOCKLE_CRITICAL_CODES = {
        "DKR0001",  # USER directive not set
        "DKR0002",  # USER specified does not exist
        "DKR0003",  # Use of sudo
        "DKR0004",  # Do not use ADD if copy available
        "DKR0006",  # Ensure COPY is used instead of ADD
        "DKR0007",  # Do not store secrets in image
        "DKR0008",  # Ensure packages are not cached
        "DKR0009",  # Do not use latest tag
    }

    DOCKLE_HIGH_CODES = {
        "DKL0001",  # Missing label maintainer
        "DKL0002",  # Missing label version
        "DKL0003",  # Missing label description
    }

    def __init__(self):
        self.dockle_path = self._find_dockle()

    def _find_dockle(self) -> str:
        """Find dockle binary."""
        for path in [
            "/usr/local/bin/dockle",
            "/usr/bin/dockle",
        ]:
            if os.path.exists(path):
                return path
        return "dockle"

    def scan(self, image_tag: str) -> list[Misconfiguration]:
        """
        Run Dockle CIS Docker benchmark check on an image.
        Returns list of misconfigurations.
        """
        findings = []

        output_file = tempfile.NamedTemporaryFile(
            mode="w+", suffix=".json", delete=False
        )
        try:
            output_path = output_file.name
            output_file.close()

            cmd = [
                self.dockle_path,
                "--format", "json",
                "--output", output_path,
                "--timeout", "120s",
                image_tag,
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=180,
            )

            if not os.path.exists(output_path) or os.path.getsize(output_path) == 0:
                logger.warning(f"Dockle produced no output for {image_tag}")
                return findings

            with open(output_path, "r") as f:
                raw = json.load(f)

            findings = self._parse_results(raw)

        except subprocess.TimeoutExpired:
            logger.error("Dockle scan timed out")
        except FileNotFoundError:
            logger.warning(
                "Dockle not found — CIS benchmark checks will be skipped. "
                "Install from: https://github.com/goodwithtech/dockle"
            )
        except json.JSONDecodeError as e:
            logger.error(f"Dockle produced invalid JSON: {e}")
        except Exception as e:
            logger.error(f"Dockle scan failed: {e}")
        finally:
            try:
                os.unlink(output_path)
            except OSError:
                pass

        return findings

    def _parse_results(self, raw: dict) -> list[Misconfiguration]:
        """Parse Dockle JSON output into Misconfiguration models."""
        findings = []

        details = raw.get("details", []) or []

        for item in details:
            code = item.get("code", "")
            title = item.get("title", "Unknown check")
            severity_str = item.get("severity", "WARN").upper()

            severity = self._map_severity(severity_str, code)

            finding = Misconfiguration(
                code=code,
                title=title,
                severity=severity,
                description=item.get("description", ""),
            )
            findings.append(finding)

        return findings

    def _map_severity(self, dockle_severity: str, code: str) -> Severity:
        """Map Dockle severity to our Severity enum with hardcoded mapping."""
        if code in self.DOCKLE_CRITICAL_CODES:
            return Severity.CRITICAL
        if code in self.DOCKLE_HIGH_CODES:
            return Severity.HIGH

        mapping = {
            "FATAL": Severity.CRITICAL,
            "WARN": Severity.HIGH,
            "INFO": Severity.LOW,
        }
        return mapping.get(dockle_severity, Severity.MEDIUM)
