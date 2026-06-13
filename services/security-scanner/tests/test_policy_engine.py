import pytest
from unittest.mock import patch, MagicMock
from src.services.policy_engine import PolicyEngine
from src.models.findings import (
    ScanDetails,
    Vulnerability,
    MalwareFinding,
    Secret,
    Misconfiguration,
    BaseImageCheck,
    SeverityBreakdown,
    Severity,
)
from src.models.scan_result import ScanStatus, Verdict


class TestPolicyEngine:
    def _make_details(
        self,
        critical=0,
        high=0,
        medium=0,
        low=0,
        malware_count=0,
        secrets_count=0,
        root_user=False,
        base_image_approved=True,
    ) -> tuple[ScanDetails, SeverityBreakdown]:
        vulns = []
        for i in range(critical):
            vulns.append(Vulnerability(
                id=f"CVE-CRIT-{i}", severity=Severity.CRITICAL,
                package="pkg", installed_version="1.0"
            ))
        for i in range(high):
            vulns.append(Vulnerability(
                id=f"CVE-HIGH-{i}", severity=Severity.HIGH,
                package="pkg", installed_version="1.0"
            ))
        for i in range(medium):
            vulns.append(Vulnerability(
                id=f"CVE-MED-{i}", severity=Severity.MEDIUM,
                package="pkg", installed_version="1.0"
            ))
        for i in range(low):
            vulns.append(Vulnerability(
                id=f"CVE-LOW-{i}", severity=Severity.LOW,
                package="pkg", installed_version="1.0"
            ))

        malware = [
            MalwareFinding(rule=f"mal{i}", file="/bad", severity=Severity.CRITICAL)
            for i in range(malware_count)
        ]
        secrets = [
            Secret(type="secret", file="config.json", description="x")
            for _ in range(secrets_count)
        ]

        misconfigs = []
        if root_user:
            misconfigs.append(Misconfiguration(
                code="DKR0001", title="USER directive not set",
                severity=Severity.CRITICAL
            ))

        base_image = None
        if not base_image_approved:
            base_image = BaseImageCheck(
                image="scratch", approved=False,
                suggestion="Use alpine:3.20 instead"
            )

        details = ScanDetails(
            vulnerabilities=vulns,
            malware=malware,
            secrets=secrets,
            misconfigurations=misconfigs,
            base_image=base_image,
        )
        breakdown = SeverityBreakdown(
            critical=critical, high=high, medium=medium, low=low
        )
        return details, breakdown

    @patch("src.services.policy_engine.check_security_tools_available")
    @patch("src.services.policy_engine.settings")
    def test_pass_clean_image(self, mock_settings, mock_tools):
        mock_tools.return_value = {"trivy": True, "clamav": True, "yara": True}
        mock_settings.BLOCK_ON_MALWARE = True
        mock_settings.BLOCK_ON_SECRETS = True

        engine = PolicyEngine()
        details, breakdown = self._make_details()
        status, verdict, reason, warnings = engine.evaluate(details, breakdown)

        assert status == ScanStatus.PASS
        assert verdict == Verdict.POLICY_PASSED
        assert reason is None
        assert warnings == []

    @patch("src.services.policy_engine.check_security_tools_available")
    @patch("src.services.policy_engine.settings")
    def test_blocked_on_excessive_critical_cve(self, mock_settings, mock_tools):
        mock_tools.return_value = {"trivy": True, "clamav": True, "yara": True}
        mock_settings.BLOCK_ON_MALWARE = True
        mock_settings.BLOCK_ON_SECRETS = True

        engine = PolicyEngine()
        details, breakdown = self._make_details(critical=51)
        status, verdict, reason, warnings = engine.evaluate(details, breakdown)

        assert status == ScanStatus.BLOCKED
        assert "Excessive vulnerabilities" in reason

    @patch("src.services.policy_engine.check_security_tools_available")
    @patch("src.services.policy_engine.settings")
    def test_blocked_on_excessive_high_cve(self, mock_settings, mock_tools):
        mock_tools.return_value = {"trivy": True, "clamav": True, "yara": True}
        mock_settings.BLOCK_ON_MALWARE = True
        mock_settings.BLOCK_ON_SECRETS = True

        engine = PolicyEngine()
        details, breakdown = self._make_details(high=501)
        status, verdict, reason, warnings = engine.evaluate(details, breakdown)

        assert status == ScanStatus.BLOCKED
        assert "Excessive vulnerabilities" in reason

    @patch("src.services.policy_engine.check_security_tools_available")
    @patch("src.services.policy_engine.settings")
    def test_warn_on_few_critical_cve(self, mock_settings, mock_tools):
        mock_tools.return_value = {"trivy": True, "clamav": True, "yara": True}
        mock_settings.BLOCK_ON_MALWARE = True
        mock_settings.BLOCK_ON_SECRETS = True

        engine = PolicyEngine()
        details, breakdown = self._make_details(critical=3)
        status, verdict, reason, warnings = engine.evaluate(details, breakdown)

        assert status == ScanStatus.PASS
        assert verdict == Verdict.ADVISORY_WARNING
        assert any("critical" in w.type.lower() for w in warnings)

    @patch("src.services.policy_engine.check_security_tools_available")
    @patch("src.services.policy_engine.settings")
    def test_blocked_on_malware(self, mock_settings, mock_tools):
        mock_tools.return_value = {"trivy": True, "clamav": True, "yara": True}
        mock_settings.BLOCK_ON_MALWARE = True
        mock_settings.BLOCK_ON_SECRETS = True

        engine = PolicyEngine()
        details, breakdown = self._make_details(malware_count=2)
        status, verdict, reason, warnings = engine.evaluate(details, breakdown)

        assert status == ScanStatus.BLOCKED
        assert "malware" in reason.lower()

    @patch("src.services.policy_engine.check_security_tools_available")
    @patch("src.services.policy_engine.settings")
    def test_blocked_on_secrets(self, mock_settings, mock_tools):
        mock_tools.return_value = {"trivy": True, "clamav": True, "yara": True}
        mock_settings.BLOCK_ON_MALWARE = True
        mock_settings.BLOCK_ON_SECRETS = True

        engine = PolicyEngine()
        details, breakdown = self._make_details(secrets_count=3)
        status, verdict, reason, warnings = engine.evaluate(details, breakdown)

        assert status == ScanStatus.BLOCKED
        assert "secret" in reason.lower()

    @patch("src.services.policy_engine.check_security_tools_available")
    @patch("src.services.policy_engine.settings")
    def test_warn_on_root_user(self, mock_settings, mock_tools):
        mock_tools.return_value = {"trivy": True, "clamav": True, "yara": True}
        mock_settings.BLOCK_ON_MALWARE = True
        mock_settings.BLOCK_ON_SECRETS = True

        engine = PolicyEngine()
        details, breakdown = self._make_details(root_user=True)
        status, verdict, reason, warnings = engine.evaluate(details, breakdown)

        assert status == ScanStatus.PASS
        assert verdict == Verdict.ADVISORY_WARNING
        assert any("root" in w.type.lower() for w in warnings)

    @patch("src.services.policy_engine.check_security_tools_available")
    @patch("src.services.policy_engine.settings")
    def test_warn_on_unapproved_base_image(self, mock_settings, mock_tools):
        mock_tools.return_value = {"trivy": True, "clamav": True, "yara": True}
        mock_settings.BLOCK_ON_MALWARE = True
        mock_settings.BLOCK_ON_SECRETS = True

        engine = PolicyEngine()
        details, breakdown = self._make_details(base_image_approved=False)
        status, verdict, reason, warnings = engine.evaluate(details, breakdown)

        assert status == ScanStatus.PASS
        assert verdict == Verdict.ADVISORY_WARNING
        assert any("base_image" in w.type.lower() for w in warnings)

    @patch("src.services.policy_engine.check_security_tools_available")
    @patch("src.services.policy_engine.settings")
    def test_multiple_block_reasons_combined(self, mock_settings, mock_tools):
        mock_tools.return_value = {"trivy": True, "clamav": True, "yara": True}
        mock_settings.BLOCK_ON_MALWARE = True
        mock_settings.BLOCK_ON_SECRETS = True

        engine = PolicyEngine()
        details, breakdown = self._make_details(
            malware_count=1, secrets_count=1
        )
        status, verdict, reason, warnings = engine.evaluate(details, breakdown)

        assert status == ScanStatus.BLOCKED
        assert ";" in reason
        assert "malware" in reason.lower()
        assert "secret" in reason.lower()

    @patch("src.services.policy_engine.check_security_tools_available")
    @patch("src.services.policy_engine.settings")
    def test_missing_tools_causes_warning(self, mock_settings, mock_tools):
        mock_tools.return_value = {"trivy": False, "clamav": False, "yara": True}
        mock_settings.BLOCK_ON_MALWARE = True
        mock_settings.BLOCK_ON_SECRETS = True

        engine = PolicyEngine()
        details, breakdown = self._make_details()
        status, verdict, reason, warnings = engine.evaluate(details, breakdown)

        assert status == ScanStatus.PASS
        assert verdict == Verdict.ADVISORY_WARNING
        assert any("scanner_unavailable" in w.type for w in warnings)
