import os
import logging
from typing import Optional

try:
    import yara
    YARA_AVAILABLE = True
except ImportError:
    YARA_AVAILABLE = False
    yara = None

from src.config import settings
from src.models.findings import MalwareFinding, Severity

logger = logging.getLogger(__name__)


class YaraScanner:
    """Custom YARA rule scanner for container-specific malware."""

    def __init__(self):
        self.rules_dir = settings.YARA_RULES_DIR
        self._compiled_rules: Optional[object] = None

    def _compile_rules(self):
        """Compile all .yara rule files in the rules directory."""
        if not YARA_AVAILABLE:
            raise RuntimeError("yara-python not installed")

        rule_files = []
        if os.path.isdir(self.rules_dir):
            for filename in os.listdir(self.rules_dir):
                if filename.endswith(".yara"):
                    rule_files.append(
                        os.path.join(self.rules_dir, filename)
                    )

        if not rule_files:
            logger.warning(f"No YARA rules found in {self.rules_dir}")
            self._compiled_rules = None
            return

        try:
            self._compiled_rules = yara.compile(filepaths={
                os.path.basename(f): f for f in rule_files
            })
            logger.info(f"Compiled {len(rule_files)} YARA rule files")
        except Exception as e:
            logger.error(f"Failed to compile YARA rules: {e}")
            self._compiled_rules = None

    def _get_matches(self, scan_path: str) -> list:
        """Run YARA matching against the scan path."""
        if os.path.isdir(scan_path):
            return self._compiled_rules.match(scan_path, timeout=120)
        if os.path.isfile(scan_path):
            return self._compiled_rules.match(scan_path, timeout=60)
        logger.warning(f"Scan path does not exist: {scan_path}")
        return []

    def _parse_severity(self, rule_meta: dict) -> Severity:
        """Parse severity from rule metadata with fallback."""
        severity_str = rule_meta.get("severity", "CRITICAL")
        try:
            return Severity(severity_str.upper())
        except ValueError:
            return Severity.CRITICAL

    def _process_file_matches(self, match, scan_path: str) -> list[MalwareFinding]:
        """Process all file matches for a single YARA match."""
        findings = []
        rule_name = match.rule
        severity = self._parse_severity(match.meta)
        category = match.meta.get("category", "malware")

        for matched_file in match.files:
            for _ in matched_file.strings:
                finding = MalwareFinding(
                    rule=rule_name,
                    file=matched_file.path or str(scan_path),
                    signature=f"yara:{rule_name}",
                    severity=severity,
                    category=category,
                )
                findings.append(finding)
                logger.warning(
                    f"YARA rule '{rule_name}' matched in "
                    f"{matched_file.path or scan_path}"
                )
        return findings

    def scan(self, scan_path: str) -> list[MalwareFinding]:
        """
        Scan a file or directory using compiled YARA rules.
        Returns list of malware findings.
        """
        if not YARA_AVAILABLE:
            logger.warning("yara-python not available — skipping YARA scan")
            return []

        if self._compiled_rules is None:
            self._compile_rules()

        if self._compiled_rules is None:
            return []

        try:
            matches = self._get_matches(scan_path)
            findings = []
            for match in matches:
                findings.extend(self._process_file_matches(match, scan_path))
        except Exception as e:
            logger.error(f"YARA scan failed: {e}")
            return []

        return findings

    def is_available(self) -> bool:
        """Check if YARA with rules is available."""
        if not YARA_AVAILABLE:
            return False
        if not os.path.isdir(self.rules_dir):
            return False
        rule_files = [
            f for f in os.listdir(self.rules_dir)
            if f.endswith(".yara")
        ]
        return len(rule_files) > 0
