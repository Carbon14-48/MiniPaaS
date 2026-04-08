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

    @patch("src.services.policy_engine.settings")
    def test_pass_clean_image(self, mock_settings):
        mock_settings.BLOCK_ON_HIGH_CVES = True
        mock_settings.BLOCK_ON_MALWARE = True
        mock_settings.BLOCK_ON_SECRETS = True
        mock_settings.BLOCK_ON_ROOT_USER = True

        engine = PolicyEngine()
        details, breakdown = self._make_details()
        status, verdict, reason, warnings = engine.evaluate(details, breakdown)

        assert status == ScanStatus.PASS
        assert verdict == Verdict.POLICY_PASSED
        assert reason is None
        assert warnings == []

    @patch("src.services.policy_engine.settings")
    def test_blocked_on_critical_cve(self, mock_settings):
        mock_settings.BLOCK_ON_HIGH_CVES = True
        mock_settings.BLOCK_ON_MALWARE = True
        mock_settings.BLOCK_ON_SECRETS = True
        mock_settings.BLOCK_ON_ROOT_USER = True

        engine = PolicyEngine()
        details, breakdown = self._make_details(critical=3)
        status, verdict, reason, warnings = engine.evaluate(details, breakdown)

        assert status == ScanStatus.BLOCKED
        assert "CRITICAL" in reason
        assert "3" in reason

    @patch("src.services.policy_engine.settings")
    def test_blocked_on_high_cve(self, mock_settings):
        mock_settings.BLOCK_ON_HIGH_CVES = True
        mock_settings.BLOCK_ON_MALWARE = True
        mock_settings.BLOCK_ON_SECRETS = True
        mock_settings.BLOCK_ON_ROOT_USER = True

        engine = PolicyEngine()
        details, breakdown = self._make_details(high=5)
        status, verdict, reason, warnings = engine.evaluate(details, breakdown)

        assert status == ScanStatus.BLOCKED
        assert "HIGH" in reason

    @patch("src.services.policy_engine.settings")
    def test_not_blocked_on_high_cve_when_disabled(self, mock_settings):
        mock_settings.BLOCK_ON_HIGH_CVES = False
        mock_settings.BLOCK_ON_MALWARE = True
        mock_settings.BLOCK_ON_SECRETS = True
        mock_settings.BLOCK_ON_ROOT_USER = True

        engine = PolicyEngine()
        details, breakdown = self._make_details(high=5)
        status, verdict, reason, warnings = engine.evaluate(details, breakdown)

        assert status == ScanStatus.PASS

    @patch("src.services.policy_engine.settings")
    def test_blocked_on_malware(self, mock_settings):
        mock_settings.BLOCK_ON_HIGH_CVES = True
        mock_settings.BLOCK_ON_MALWARE = True
        mock_settings.BLOCK_ON_SECRETS = True
        mock_settings.BLOCK_ON_ROOT_USER = True

        engine = PolicyEngine()
        details, breakdown = self._make_details(malware_count=2)
        status, verdict, reason, warnings = engine.evaluate(details, breakdown)

        assert status == ScanStatus.BLOCKED
        assert "malware" in reason.lower()

    @patch("src.services.policy_engine.settings")
    def test_blocked_on_secrets(self, mock_settings):
        mock_settings.BLOCK_ON_HIGH_CVES = True
        mock_settings.BLOCK_ON_MALWARE = True
        mock_settings.BLOCK_ON_SECRETS = True
        mock_settings.BLOCK_ON_ROOT_USER = True

        engine = PolicyEngine()
        details, breakdown = self._make_details(secrets_count=3)
        status, verdict, reason, warnings = engine.evaluate(details, breakdown)

        assert status == ScanStatus.BLOCKED
        assert "secret" in reason.lower()

    @patch("src.services.policy_engine.settings")
    def test_blocked_on_root_user(self, mock_settings):
        mock_settings.BLOCK_ON_HIGH_CVES = True
        mock_settings.BLOCK_ON_MALWARE = True
        mock_settings.BLOCK_ON_SECRETS = True
        mock_settings.BLOCK_ON_ROOT_USER = True

        engine = PolicyEngine()
        details, breakdown = self._make_details(root_user=True)
        status, verdict, reason, warnings = engine.evaluate(details, breakdown)

        assert status == ScanStatus.BLOCKED
        assert "root" in reason.lower()

    @patch("src.services.policy_engine.settings")
    def test_blocked_on_unapproved_base_image(self, mock_settings):
        mock_settings.BLOCK_ON_HIGH_CVES = True
        mock_settings.BLOCK_ON_MALWARE = True
        mock_settings.BLOCK_ON_SECRETS = True
        mock_settings.BLOCK_ON_ROOT_USER = True

        engine = PolicyEngine()
        details, breakdown = self._make_details(base_image_approved=False)
        status, verdict, reason, warnings = engine.evaluate(details, breakdown)

        assert status == ScanStatus.BLOCKED
        assert "base image" in reason.lower()

    @patch("src.services.policy_engine.settings")
    def test_warn_on_medium_only(self, mock_settings):
        mock_settings.BLOCK_ON_HIGH_CVES = True
        mock_settings.BLOCK_ON_MALWARE = True
        mock_settings.BLOCK_ON_SECRETS = True
        mock_settings.BLOCK_ON_ROOT_USER = True

        engine = PolicyEngine()
        details, breakdown = self._make_details(medium=5)
        status, verdict, reason, warnings = engine.evaluate(details, breakdown)

        assert status == ScanStatus.WARN
        assert verdict == Verdict.ADVISORY_WARNING
        assert reason is None
        assert len(warnings) > 0

    @patch("src.services.policy_engine.settings")
    def test_warn_on_low_only(self, mock_settings):
        mock_settings.BLOCK_ON_HIGH_CVES = True
        mock_settings.BLOCK_ON_MALWARE = True
        mock_settings.BLOCK_ON_SECRETS = True
        mock_settings.BLOCK_ON_ROOT_USER = True

        engine = PolicyEngine()
        details, breakdown = self._make_details(low=10)
        status, verdict, reason, warnings = engine.evaluate(details, breakdown)

        assert status == ScanStatus.WARN
        assert any("low" in w.type.lower() for w in warnings)

    @patch("src.services.policy_engine.settings")
    def test_multiple_block_reasons_combined(self, mock_settings):
        mock_settings.BLOCK_ON_HIGH_CVES = True
        mock_settings.BLOCK_ON_MALWARE = True
        mock_settings.BLOCK_ON_SECRETS = True
        mock_settings.BLOCK_ON_ROOT_USER = True

        engine = PolicyEngine()
        details, breakdown = self._make_details(
            critical=1, secrets_count=1, base_image_approved=False
        )
        status, verdict, reason, warnings = engine.evaluate(details, breakdown)

        assert status == ScanStatus.BLOCKED
        assert ";" in reason
        assert "CRITICAL" in reason
        assert "secret" in reason.lower()
        assert "base image" in reason.lower()
