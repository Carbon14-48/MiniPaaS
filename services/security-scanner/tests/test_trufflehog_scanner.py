import pytest
from unittest.mock import patch, MagicMock
from src.scanners.trufflehog_scanner import TruffleHogScanner


class TestTruffleHogScanner:
    @patch("os.path.exists", return_value=True)
    @patch("src.scanners.trufflehog_scanner.subprocess.run")
    @patch("src.scanners.trufflehog_scanner.tempfile.NamedTemporaryFile")
    def test_scan_detects_secrets(self, mock_tempfile, mock_run, mock_exists):
        mock_file = MagicMock()
        mock_file.name = "/tmp/scan_output.jsonl"
        mock_tempfile.return_value = mock_file

        aws_entry = '{"DetectorName":"AWS","DetectorType":"AWS","Raw":"AKIAIOSFODNN7EXAMPLE","SourceMetadata":{"SourceID":"config.json","Data":{"line":12}}}'
        github_entry = '{"DetectorName":"GitHub","DetectorType":"GitHub","Raw":"ghp_xxxx","SourceMetadata":{"SourceID":".env","Data":{"line":3}}}'
        output = f"{aws_entry}\n{github_entry}\n"

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = output
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        scanner = TruffleHogScanner()
        scanner._trufflehog_path = "trufflehog"
        findings = scanner.scan("/tmp/scan_dir")

        assert len(findings) == 2
        assert findings[0].type == "AWS"
        assert "config.json" in findings[0].file
        assert findings[1].type == "GitHub"

    @patch("os.path.exists", return_value=True)
    @patch("src.scanners.trufflehog_scanner.subprocess.run")
    @patch("src.scanners.trufflehog_scanner.tempfile.NamedTemporaryFile")
    def test_scan_no_secrets_returns_empty(self, mock_tempfile, mock_run, mock_exists):
        mock_file = MagicMock()
        mock_file.name = "/tmp/scan_output.jsonl"
        mock_tempfile.return_value = mock_file

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = ""
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        scanner = TruffleHogScanner()
        scanner._trufflehog_path = "trufflehog"
        findings = scanner.scan("/tmp/scan_dir")

        assert len(findings) == 0

    @patch("os.path.exists", return_value=True)
    @patch("src.scanners.trufflehog_scanner.subprocess.run")
    @patch("src.scanners.trufflehog_scanner.tempfile.NamedTemporaryFile")
    def test_scan_skips_invalid_json_lines(self, mock_tempfile, mock_run, mock_exists):
        mock_file = MagicMock()
        mock_file.name = "/tmp/scan_output.jsonl"
        mock_tempfile.return_value = mock_file

        valid_entry = '{"DetectorName":"AWS","DetectorType":"AWS","Raw":"xxx","SourceMetadata":{"SourceID":"file.txt","Data":{}}}'
        output = f"not valid json\n{valid_entry}\n"

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = output
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        scanner = TruffleHogScanner()
        scanner._trufflehog_path = "trufflehog"
        findings = scanner.scan("/tmp/scan_dir")

        assert len(findings) == 1
        assert findings[0].type == "AWS"

    @patch("os.path.exists", return_value=True)
    @patch("src.scanners.trufflehog_scanner.subprocess.run")
    @patch("src.scanners.trufflehog_scanner.tempfile.NamedTemporaryFile")
    def test_scan_returns_empty_on_nonexistent_path(self, mock_tempfile, mock_run, mock_exists):
        mock_exists.return_value = False

        scanner = TruffleHogScanner()
        scanner._trufflehog_path = "trufflehog"
        findings = scanner.scan("/nonexistent")

        assert len(findings) == 0
