import json
import subprocess
import tempfile
import os
import logging

from src.config import settings
from src.models.findings import Vulnerability, Severity

logger = logging.getLogger(__name__)


class TrivyScanner:
    """CVE scanner using Trivy — scans OS packages and language dependencies."""

    def __init__(self):
        self.trivy_path = settings.TRIVY_PATH

    def scan(self, image_tag: str) -> list[Vulnerability]:
        """
        Run Trivy image scan and return parsed vulnerabilities.
        Uses --scanners vuln to only run vulnerability detection.
        Uses --format json for machine-readable output.
        """
        output_file = tempfile.NamedTemporaryFile(
            mode="w+", suffix=".json", delete=False
        )
        try:
            output_path = output_file.name
            output_file.close()

            cmd = [
                self.trivy_path,
                "image",
                "--quiet",
                "--scanners", "vuln",
                "--format", "json",
                "--output", output_path,
                "--timeout", "180s",
                image_tag,
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=settings.SCANNER_MAX_TIMEOUT,
            )

            if not os.path.exists(output_path) or os.path.getsize(output_path) == 0:
                logger.warning(
                    f"Trivy produced no output for {image_tag}. "
                    f"stderr: {result.stderr[:500]}"
                )
                return []

            with open(output_path, "r") as f:
                raw = json.load(f)

            return self._parse_results(raw, image_tag)

        except subprocess.TimeoutExpired:
            logger.error(f"Trivy scan timed out for {image_tag}")
            return []
        except json.JSONDecodeError as e:
            logger.error(f"Trivy produced invalid JSON for {image_tag}: {e}")
            return []
        except FileNotFoundError:
            logger.error(
                f"Trivy binary not found at {self.trivy_path}. "
                "Ensure it is installed in the container."
            )
            return []
        except Exception as e:
            logger.error(f"Trivy scan failed for {image_tag}: {e}")
            return []
        finally:
            try:
                os.unlink(output_path)
            except OSError:
                pass

    def _parse_results(
        self, raw: dict, image_tag: str
    ) -> list[Vulnerability]:
        """Parse Trivy JSON output into Vulnerability models."""
        vulnerabilities = []

        results = raw.get("Results", [])
        for result in results:
            vulnerabilities_data = result.get("Vulnerabilities", []) or []
            for vuln in vulnerabilities_data:
                try:
                    vuln_obj = Vulnerability(
                        id=vuln.get("VulnerabilityID", "UNKNOWN"),
                        severity=self._map_severity(vuln.get("Severity", "UNKNOWN")),
                        package=vuln.get("PkgName", vuln.get("PackageName", "unknown")),
                        installed_version=vuln.get("InstalledVersion", "unknown"),
                        fixed_version=vuln.get("FixedVersion"),
                        description=vuln.get("Description", ""),
                        title=vuln.get("Title"),
                    )
                    vulnerabilities.append(vuln_obj)
                except Exception as e:
                    logger.warning(f"Failed to parse vulnerability: {e}")
                    continue

        return vulnerabilities

    def _map_severity(self, trivy_severity: str) -> Severity:
        """Map Trivy severity strings to our Severity enum."""
        mapping = {
            "CRITICAL": Severity.CRITICAL,
            "HIGH": Severity.HIGH,
            "MEDIUM": Severity.MEDIUM,
            "LOW": Severity.LOW,
            "UNKNOWN": Severity.UNKNOWN,
        }
        return mapping.get(trivy_severity.upper(), Severity.UNKNOWN)
