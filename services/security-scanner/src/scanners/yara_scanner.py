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

    def scan(self, scan_path: str) -> list[MalwareFinding]:
        """
        Scan a file or directory using compiled YARA rules.
        Returns list of malware findings.
        """
        findings = []

        if not YARA_AVAILABLE:
            logger.warning("yara-python not available — skipping YARA scan")
            return findings

        if self._compiled_rules is None:
            self._compile_rules()

        if self._compiled_rules is None:
            return findings

        try:
            if os.path.isdir(scan_path):
                matches = self._compiled_rules.match(scan_path, timeout=120)
            elif os.path.isfile(scan_path):
                matches = self._compiled_rules.match(scan_path, timeout=60)
            else:
                logger.warning(f"Scan path does not exist: {scan_path}")
                return findings

            for match in matches:
                rule_meta = match.meta
                rule_name = match.rule

                severity_str = rule_meta.get("severity", "CRITICAL")
                try:
                    severity = Severity(severity_str.upper())
                except ValueError:
                    severity = Severity.CRITICAL

                category = rule_meta.get("category", "malware")
                description = rule_meta.get("description", f"YARA rule matched: {rule_name}")

                for matched_file in match.files:
                    for string_match in matched_file.strings:
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

        except Exception as e:
            logger.error(f"YARA scan failed: {e}")

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
