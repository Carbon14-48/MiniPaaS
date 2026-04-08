import pytest
from src.scanners.trivy_scanner import TrivyScanner
from src.models.findings import Severity


class TestTrivyScanner:
    def test_parse_parses_critical_and_high_vulns(self):
        scanner = TrivyScanner()
        raw = {
            "Results": [
                {
                    "Vulnerabilities": [
                        {
                            "VulnerabilityID": "CVE-2024-3094",
                            "Severity": "CRITICAL",
                            "PkgName": "liblzma",
                            "InstalledVersion": "5.6.0",
                            "FixedVersion": "6.4",
                            "Description": "XZ backdoor",
                        },
                        {
                            "VulnerabilityID": "CVE-2023-5678",
                            "Severity": "HIGH",
                            "PkgName": "openssl",
                            "InstalledVersion": "1.0.0",
                            "FixedVersion": "1.1.1",
                            "Description": "OpenSSL RCE",
                        },
                    ]
                }
            ]
        }

        results = scanner._parse_results(raw, "test-image")

        assert len(results) == 2
        assert results[0].id == "CVE-2024-3094"
        assert results[0].severity == Severity.CRITICAL
        assert results[0].package == "liblzma"
        assert results[0].fixed_version == "6.4"

        assert results[1].id == "CVE-2023-5678"
        assert results[1].severity == Severity.HIGH
        assert results[1].package == "openssl"

    def test_parse_handles_empty_vuln_list(self):
        scanner = TrivyScanner()
        raw = {"Results": [{"Vulnerabilities": []}]}
        results = scanner._parse_results(raw, "clean-image")
        assert len(results) == 0

    def test_parse_handles_all_severities(self):
        scanner = TrivyScanner()
        raw = {
            "Results": [
                {
                    "Vulnerabilities": [
                        {"VulnerabilityID": "C-1", "Severity": "CRITICAL", "PkgName": "p1", "InstalledVersion": "1.0"},
                        {"VulnerabilityID": "H-1", "Severity": "HIGH", "PkgName": "p2", "InstalledVersion": "2.0"},
                        {"VulnerabilityID": "M-1", "Severity": "MEDIUM", "PkgName": "p3", "InstalledVersion": "3.0"},
                        {"VulnerabilityID": "L-1", "Severity": "LOW", "PkgName": "p4", "InstalledVersion": "4.0"},
                        {"VulnerabilityID": "U-1", "Severity": "UNKNOWN", "PkgName": "p5", "InstalledVersion": "5.0"},
                    ]
                }
            ]
        }

        results = scanner._parse_results(raw, "test-image")

        assert len(results) == 5
        severities = {r.severity for r in results}
        assert severities == {
            Severity.CRITICAL, Severity.HIGH,
            Severity.MEDIUM, Severity.LOW, Severity.UNKNOWN,
        }

    def test_parse_uses_pkgname_fallback(self):
        scanner = TrivyScanner()
        raw = {
            "Results": [
                {
                    "Vulnerabilities": [
                        {
                            "VulnerabilityID": "CVE-1",
                            "Severity": "HIGH",
                            "PackageName": "fallback_pkg",
                            "InstalledVersion": "1.0",
                        },
                    ]
                }
            ]
        }
        results = scanner._parse_results(raw, "test-image")
        assert len(results) == 1
        assert results[0].package == "fallback_pkg"

    def test_parse_handles_missing_fields_gracefully(self):
        scanner = TrivyScanner()
        raw = {"Results": [{"Vulnerabilities": [{"VulnerabilityID": "CVE-1"}]}]}
        results = scanner._parse_results(raw, "test-image")
        assert len(results) == 1
        assert results[0].package == "unknown"
        assert results[0].installed_version == "unknown"

    def test_severity_mapping_all_cases(self):
        scanner = TrivyScanner()
        assert scanner._map_severity("CRITICAL") == Severity.CRITICAL
        assert scanner._map_severity("HIGH") == Severity.HIGH
        assert scanner._map_severity("MEDIUM") == Severity.MEDIUM
        assert scanner._map_severity("LOW") == Severity.LOW
        assert scanner._map_severity("UNKNOWN") == Severity.UNKNOWN
        assert scanner._map_severity("invalid") == Severity.UNKNOWN
        assert scanner._map_severity("HIGH") == Severity.HIGH
