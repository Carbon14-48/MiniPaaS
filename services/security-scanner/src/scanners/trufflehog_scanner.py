import json
import subprocess
import tempfile
import os
import logging
import shutil
import re
from pathlib import Path

from src.config import settings
from src.models.findings import Secret

logger = logging.getLogger(__name__)

SECRET_PATTERNS = {
    ".env": re.compile(r"^[\w]+\s*=\s*[\"']?[\w\-\_\./+]+[\"']?$", re.MULTILINE),
    ".env": re.compile(r"(AWS_SECRET_ACCESS_KEY|AWS_ACCESS_KEY_ID|DATABASE_URL|POSTGRES_PASSWORD|MONGO_URI|SECRET_KEY|API_KEY|TOKEN|PASSWORD)\s*=\s*[\"']?[\w\-\_\./+]+[\"']?", re.IGNORECASE),
    ".aws": re.compile(r"(aws_access_key_id|aws_secret_access_key)\s*=\s*[\"']?[\w\-\_]+[\"']?", re.IGNORECASE),
    ".pem": re.compile(r"-----BEGIN (RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----"),
    ".key": re.compile(r"-----BEGIN (RSA |EC |DSA )?PRIVATE KEY-----"),
    "config": re.compile(r"(api_key|apiKey|secret|password|token)\s*[:=]\s*[\"']?[\w\-\_\./+]+[\"']?", re.IGNORECASE),
}


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
        Also scans for common secret file patterns.
        """
        findings = []

        if not os.path.exists(scan_path):
            logger.warning(f"Scan path does not exist: {scan_path}")
            return findings

        try:
            cmd = [
                self._trufflehog_path,
                "filesystem",
                scan_path,
                "--json",
                "--no-update",
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,
            )

            output = result.stdout + "\n" + result.stderr

            for line in output.splitlines():
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                    if "DetectorType" in entry or "DetectorName" in entry:
                        secret = self._parse_entry(entry)
                        if secret:
                            findings.append(secret)
                except json.JSONDecodeError:
                    continue

            logger.info(f"TruffleHog found {len(findings)} secrets")

        except subprocess.TimeoutExpired:
            logger.error("TruffleHog scan timed out")
        except FileNotFoundError:
            logger.warning(
                "TruffleHog not found — using fallback pattern scan"
            )
            findings.extend(self._fallback_scan(scan_path))
        except Exception as e:
            logger.error(f"TruffleHog scan failed: {e}")
            findings.extend(self._fallback_scan(scan_path))

        return findings

    def _fallback_scan(self, scan_path: str) -> list[Secret]:
        """Fallback scan using regex patterns when TruffleHog is unavailable."""
        findings = []
        
        secret_file_patterns = [
            ".env",
            ".env.*",
            ".aws/**",
            "*.pem",
            "*.key",
            "id_rsa",
            "id_ed25519",
            "credentials",
            ".git-credentials",
            ".npmrc",
            ".pypirc",
            "config.json",
            "secrets.yaml",
            "secrets.yml",
            "secrets.toml",
        ]
        
        try:
            for root, dirs, files in os.walk(scan_path):
                depth = root[len(scan_path):].count(os.sep)
                if depth > 5:
                    dirs.clear()
                    continue
                
                for filename in files:
                    filepath = os.path.join(root, filename)
                    rel_path = os.path.relpath(filepath, scan_path)
                    
                    should_scan = False
                    for pattern in secret_file_patterns:
                        if self._match_pattern(filename, pattern) or self._match_pattern(rel_path, pattern):
                            should_scan = True
                            break
                    
                    if should_scan and os.path.getsize(filepath) < 1024 * 1024:
                        try:
                            content = Path(filepath).read_text(errors="ignore")
                            for secret_type, pattern in SECRET_PATTERNS.items():
                                matches = pattern.finditer(content)
                                for match in matches:
                                    findings.append(Secret(
                                        type=secret_type,
                                        file=rel_path,
                                        line=match.start(),
                                        description=f"Pattern match: {match.group()[:50]}",
                                        matched_value=match.group()[:50],
                                    ))
                        except Exception as e:
                            logger.debug(f"Could not read {filepath}: {e}")
        except Exception as e:
            logger.error(f"Fallback scan failed: {e}")
        
        if findings:
            logger.info(f"Fallback scan found {len(findings)} secrets")
        return findings

    def _match_pattern(self, name: str, pattern: str) -> bool:
        """Simple glob-like pattern matching."""
        import fnmatch
        return fnmatch.fnmatch(name.lower(), pattern.lower()) or fnmatch.fnmatch(name, pattern)

    def _parse_entry(self, entry: dict) -> Secret | None:
        """Parse a TruffleHog JSON entry into a Secret model."""
        try:
            detector_name = entry.get("DetectorName", "unknown")
            detector_type = entry.get("DetectorType", None)
            
            detector = detector_name
            if detector == "unknown" and detector_type:
                detector = str(detector_type)
            
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
                description=f"TruffleHog detected {detector}",
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
