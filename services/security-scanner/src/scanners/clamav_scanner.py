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

        if not self.is_available():
            logger.warning(
                "ClamAV not available or no database — skipping scan. "
                "Run 'freshclam' to download signatures."
            )
            return findings

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

            output = result.stdout + "\n" + result.stderr

            findings = self._parse_output(output)

        except subprocess.TimeoutExpired:
            logger.error("ClamAV scan timed out")
        except FileNotFoundError:
            logger.error("clamscan binary not found — ClamAV not installed")
        except Exception as e:
            logger.error(f"ClamAV scan failed: {e}")

        return findings

    def _parse_output(self, output: str) -> list[MalwareFinding]:
        """Parse ClamAV output and extract real malware findings."""
        findings = []
        non_malware_prefixes = (
            "No ", "ERROR", "LibClamAV", "clamscan: ",
            "stream:", "Can't", "I/O", "database",
        )

        for line in output.splitlines():
            if not line.strip():
                continue

            # Skip non-malware lines
            if any(line.startswith(p) for p in non_malware_prefixes):
                continue

            line_lower = line.lower()
            if "FOUND" in line_upper if (line_upper := line.upper()) else False:
                parts = line.split(":")
                if len(parts) >= 2:
                    file_path = parts[0].strip()
                    signature = ":".join(parts[1:]).strip().replace("FOUND", "").strip()

                    if file_path and signature:
                        findings.append(MalwareFinding(
                            rule=f"clamav:{signature}",
                            file=file_path,
                            signature=signature,
                            severity=Severity.CRITICAL,
                            category="malware",
                        ))
                        logger.warning(
                            f"ClamAV detected malware: {file_path} — {signature}"
                        )

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
        except FileNotFoundError:
            logger.error("freshclam not found")
            return False
        except Exception as e:
            logger.error(f"Failed to update ClamAV DB: {e}")
            return False

    def is_available(self) -> bool:
        """Check if ClamAV is properly installed and databases exist."""
        try:
            db_main = os.path.join(self.clamav_db, "main.cvd")
            db_cld = os.path.join(self.clamav_db, "main.cld")
            db_cld2 = os.path.join(self.clamav_db, "main.cld")
            if not (os.path.exists(db_main) or os.path.exists(db_cld)):
                logger.warning(
                    f"ClamAV database not found at {self.clamav_db}. "
                    f"Run 'freshclam' to download signatures."
                )
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
