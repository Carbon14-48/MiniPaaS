import subprocess
import tempfile
import os
import logging

from src.config import settings
from src.models.findings import MalwareFinding, Severity

logger = logging.getLogger(__name__)


class ClamavScanner:
    """Malware scanner using ClamAV — signature-based detection of known malware."""

    def __init__(self):
        self.clamav_db = settings.CLAMAV_DB_PATH

    def scan(self, image_tag: str, extract_dir: str) -> list[MalwareFinding]:
        """
        Scan extracted image layers with ClamAV.
        Uses clamscan on the extracted directory.
        Returns list of detected malware.
        """
        findings = []

        if not os.path.isdir(extract_dir):
            logger.warning(f"Extraction directory does not exist: {extract_dir}")
            return findings

        try:
            cmd = [
                "clamscan",
                "--recursive",
                "--infected",
                "--no-summary",
                "--max-filesize=100M",
                "--max-scansize=500M",
                "--database", self.clamav_db,
                extract_dir,
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,
            )

            output = result.stdout + result.stderr

            for line in output.splitlines():
                line_lower = line.lower()
                if "found" in line_lower or "clamav:" in line_lower:
                    parts = line.split(":")
                    if len(parts) >= 3:
                        file_path = parts[1].strip()
                        signature_raw = ":".join(parts[2:]).strip()

                        if file_path and signature_raw:
                            finding = MalwareFinding(
                                rule=f"clamav:{signature_raw}",
                                file=file_path,
                                signature=signature_raw,
                                severity=Severity.CRITICAL,
                                category="malware",
                            )
                            findings.append(finding)
                            logger.warning(
                                f"ClamAV detected malware: {file_path} — {signature_raw}"
                            )

        except subprocess.TimeoutExpired:
            logger.error("ClamAV scan timed out")
        except FileNotFoundError:
            logger.error("clamscan binary not found — ClamAV not installed")
        except Exception as e:
            logger.error(f"ClamAV scan failed: {e}")

        return findings

    def update_db(self) -> bool:
        """Update ClamAV signature database via freshclam."""
        try:
            result = subprocess.run(
                ["freshclam", "--quiet"],
                capture_output=True,
                text=True,
                timeout=120,
            )
            if result.returncode == 0:
                logger.info("ClamAV database updated successfully")
                return True
            else:
                logger.warning(f"freshclam failed: {result.stderr}")
                return False
        except Exception as e:
            logger.error(f"Failed to update ClamAV DB: {e}")
            return False

    def is_available(self) -> bool:
        """Check if ClamAV is properly installed and databases exist."""
        try:
            db_main = os.path.join(self.clamav_db, "main.cvd")
            db_cld = os.path.join(self.clamav_db, "main.cld")
            if not (os.path.exists(db_main) or os.path.exists(db_cld)):
                return False
            result = subprocess.run(
                ["clamscan", "--version"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            return result.returncode == 0
        except Exception:
            return False
