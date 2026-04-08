import json
import subprocess
import tempfile
import os
import logging
import shutil

from src.config import settings
from src.models.findings import Secret

logger = logging.getLogger(__name__)


class TruffleHogScanner:
    """Secrets scanner using TruffleHog v3 — detects credentials in image layers."""

    def __init__(self):
        self._trufflehog_path = self._find_trufflehog()

    def _find_trufflehog(self) -> str:
        """Find trufflehog binary."""
        for path in [
            "/usr/local/bin/trufflehog",
            "/usr/bin/trufflehog",
            shutil.which("trufflehog"),
        ]:
            if path and os.path.exists(path):
                return path
        return "trufflehog"

    def scan(self, scan_path: str) -> list[Secret]:
        """
        Run TruffleHog filesystem scan to detect secrets in image layers.
        Uses JSON output for machine-readable results.
        """
        findings = []

        if not os.path.exists(scan_path):
            logger.warning(f"Scan path does not exist: {scan_path}")
            return findings

        output_file = tempfile.NamedTemporaryFile(
            mode="w+", suffix=".jsonl", delete=False
        )
        output_file.close()

        try:
            cmd = [
                self._trufflehog_path,
                "filesystem",
                scan_path,
                "--json",
                "--no-update",
                "--max-depth=10",
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,
            )

            output = result.stdout + result.stderr

            for line in output.splitlines():
                if not line.strip():
                    continue
                try:
                    entry = json.loads(line)
                    secret = self._parse_entry(entry)
                    if secret:
                        findings.append(secret)
                except json.JSONDecodeError:
                    continue

        except subprocess.TimeoutExpired:
            logger.error("TruffleHog scan timed out")
        except FileNotFoundError:
            logger.warning(
                "TruffleHog not found — secrets detection will be skipped. "
                "Install with: go install github.com/trufflesecurity/trufflehog@latest"
            )
        except Exception as e:
            logger.error(f"TruffleHog scan failed: {e}")
        finally:
            try:
                os.unlink(output_file.name)
            except OSError:
                pass

        return findings

    def _parse_entry(self, entry: dict) -> Secret | None:
        """Parse a TruffleHog JSON entry into a Secret model."""
        try:
            raw_detector = entry.get("DetectorName", "unknown")
            detector = entry.get("DetectorType", raw_detector)
            file_path = entry.get("SourceMetadata", {}).get(
                "SourceID", "unknown"
            )

            extra = entry.get("ExtraData", {})
            line_info = entry.get("SourceMetadata", {}).get("Data", {}).get(
                "line", None
            )

            matched_value = entry.get("Raw", "")
            if len(matched_value) > 80:
                matched_value = matched_value[:80] + "..."

            return Secret(
                type=str(detector),
                file=str(file_path),
                line=line_info,
                description=f"TruffleHog detected {detector} — {raw_detector}",
                matched_value=matched_value,
            )
        except Exception as e:
            logger.warning(f"Failed to parse TruffleHog entry: {e}")
            return None

    def is_available(self) -> bool:
        """Check if TruffleHog binary is installed."""
        try:
            result = subprocess.run(
                [self._trufflehog_path, "--version"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            return result.returncode == 0
        except Exception:
            return False
