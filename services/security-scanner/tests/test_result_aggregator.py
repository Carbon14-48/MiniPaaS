import pytest
from unittest.mock import patch, MagicMock
from src.models.findings import (
    Vulnerability,
    Secret,
    MalwareFinding,
    Misconfiguration,
    Severity,
)
from src.services.result_aggregator import ResultAggregator


class TestResultAggregator:
    def test_aggregate_empty_results(self):
        aggregator = ResultAggregator()
        details, breakdown = aggregator.aggregate(
            vulnerabilities=[],
            malware=[],
            secrets=[],
            misconfigurations=[],
            base_image=None,
        )
        assert breakdown.critical == 0
        assert breakdown.high == 0
        assert breakdown.medium == 0
        assert breakdown.low == 0
        assert breakdown.total() == 0
        assert len(details.vulnerabilities) == 0
        assert len(details.malware) == 0
        assert len(details.secrets) == 0
        assert len(details.misconfigurations) == 0

    def test_aggregate_vulnerabilities_severity_counts(self):
        aggregator = ResultAggregator()
        vulns = [
            Vulnerability(id="CVE-1", severity=Severity.CRITICAL, package="pkg1", installed_version="1.0"),
            Vulnerability(id="CVE-2", severity=Severity.CRITICAL, package="pkg2", installed_version="2.0"),
            Vulnerability(id="CVE-3", severity=Severity.HIGH, package="pkg3", installed_version="3.0"),
            Vulnerability(id="CVE-4", severity=Severity.MEDIUM, package="pkg4", installed_version="4.0"),
            Vulnerability(id="CVE-5", severity=Severity.LOW, package="pkg5", installed_version="5.0"),
        ]
        details, breakdown = aggregator.aggregate(
            vulnerabilities=vulns,
            malware=[],
            secrets=[],
            misconfigurations=[],
            base_image=None,
        )
        assert breakdown.critical == 2
        assert breakdown.high == 1
        assert breakdown.medium == 1
        assert breakdown.low == 1
        assert breakdown.has_critical_or_high() is True
        assert breakdown.total() == 5

    def test_aggregate_malware(self):
        aggregator = ResultAggregator()
        malware = [
            MalwareFinding(
                rule="crypto_miner_xmrig",
                file="/usr/bin/xmrig",
                severity=Severity.CRITICAL,
            )
        ]
        details, _ = aggregator.aggregate(
            vulnerabilities=[],
            malware=malware,
            secrets=[],
            misconfigurations=[],
            base_image=None,
        )
        assert len(details.malware) == 1
        assert details.malware[0].rule == "crypto_miner_xmrig"

    def test_aggregate_secrets(self):
        aggregator = ResultAggregator()
        secrets = [
            Secret(type="aws_access_key", file="config.json", description="AWS key")
        ]
        details, _ = aggregator.aggregate(
            vulnerabilities=[],
            malware=[],
            secrets=secrets,
            misconfigurations=[],
            base_image=None,
        )
        assert len(details.secrets) == 1
        assert details.secrets[0].type == "aws_access_key"

    def test_aggregate_misconfigurations(self):
        aggregator = ResultAggregator()
        misconfigs = [
            Misconfiguration(code="DKR0001", title="USER directive not set", severity=Severity.CRITICAL)
        ]
        details, _ = aggregator.aggregate(
            vulnerabilities=[],
            malware=[],
            secrets=[],
            misconfigurations=misconfigs,
            base_image=None,
        )
        assert len(details.misconfigurations) == 1
        assert details.misconfigurations[0].code == "DKR0001"

    def test_aggregate_no_critical_or_high(self):
        aggregator = ResultAggregator()
        vulns = [
            Vulnerability(id="CVE-1", severity=Severity.MEDIUM, package="pkg", installed_version="1.0"),
            Vulnerability(id="CVE-2", severity=Severity.LOW, package="pkg", installed_version="1.0"),
        ]
        _, breakdown = aggregator.aggregate(
            vulnerabilities=vulns,
            malware=[],
            secrets=[],
            misconfigurations=[],
            base_image=None,
        )
        assert breakdown.has_critical_or_high() is False

    def test_aggregate_orders_vulnerabilities_by_severity(self):
        aggregator = ResultAggregator()
        vulns = [
            Vulnerability(id="CVE-MED", severity=Severity.MEDIUM, package="pkg", installed_version="1.0"),
            Vulnerability(id="CVE-CRIT", severity=Severity.CRITICAL, package="pkg", installed_version="1.0"),
            Vulnerability(id="CVE-LOW", severity=Severity.LOW, package="pkg", installed_version="1.0"),
        ]
        details, _ = aggregator.aggregate(
            vulnerabilities=vulns,
            malware=[],
            secrets=[],
            misconfigurations=[],
            base_image=None,
        )
        assert details.vulnerabilities[0].id == "CVE-CRIT"
        assert details.vulnerabilities[1].id == "CVE-MED"
        assert details.vulnerabilities[2].id == "CVE-LOW"
