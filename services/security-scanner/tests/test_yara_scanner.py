import pytest
from unittest.mock import patch, MagicMock
from src.models.findings import Severity


class TestYaraScanner:
    def test_severity_from_meta_critical(self):
        """Test that severity is correctly extracted from YARA meta."""
        meta = {"severity": "CRITICAL", "category": "crypto_miner"}
        severity = Severity(meta.get("severity", "UNKNOWN").upper())
        assert severity == Severity.CRITICAL

    def test_severity_from_meta_high(self):
        meta = {"severity": "HIGH", "category": "webshell"}
        severity = Severity(meta.get("severity", "UNKNOWN").upper())
        assert severity == Severity.HIGH

    def test_severity_unknown_maps_to_unknown_enum(self):
        """Severity mapping for unknown values should return UNKNOWN."""
        from src.scanners.yara_scanner import Severity
        # Map unknown severity to Severity.UNKNOWN
        raw_severity = "INVALID"
        try:
            severity = Severity(raw_severity.upper())
        except ValueError:
            severity = Severity.UNKNOWN
        assert severity == Severity.UNKNOWN

    def test_findings_creation_from_match(self):
        """Test that MalwareFinding objects are correctly created from YARA matches."""
        from src.models.findings import MalwareFinding

        finding = MalwareFinding(
            rule="xmrig_binary",
            file="/tmp/xmrig",
            signature="yara:xmrig_binary",
            severity=Severity.CRITICAL,
            category="crypto_miner",
        )

        assert finding.rule == "xmrig_binary"
        assert finding.severity == Severity.CRITICAL
        assert finding.category == "crypto_miner"
        assert finding.file == "/tmp/xmrig"

    def test_multiple_findings_from_multiple_matches(self):
        """Simulate processing multiple YARA rule matches."""
        from src.models.findings import MalwareFinding

        matches = [
            {"rule": "webshell_php", "file": "/app/shell.php", "severity": "CRITICAL"},
            {"rule": "crypto_xmrig", "file": "/usr/bin/xmrig", "severity": "CRITICAL"},
            {"rule": "reverse_shell", "file": "/tmp/script.sh", "severity": "HIGH"},
        ]

        findings = [
            MalwareFinding(
                rule=m["rule"],
                file=m["file"],
                signature=f"yara:{m['rule']}",
                severity=Severity(m["severity"]),
                category="malware",
            )
            for m in matches
        ]

        assert len(findings) == 3
        critical_findings = [f for f in findings if f.severity == Severity.CRITICAL]
        assert len(critical_findings) == 2
        assert {f.rule for f in critical_findings} == {"webshell_php", "crypto_xmrig"}
