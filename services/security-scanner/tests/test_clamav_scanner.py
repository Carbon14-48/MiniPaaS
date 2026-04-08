import pytest
from src.scanners.clamav_scanner import ClamavScanner


class TestClamavScanner:
    def test_is_available_returns_bool(self):
        """is_available() should return a boolean."""
        scanner = ClamavScanner()
        result = scanner.is_available()
        assert isinstance(result, bool)

    def test_update_db_returns_bool(self):
        """update_db() should return a boolean."""
        scanner = ClamavScanner()
        result = scanner.update_db()
        assert isinstance(result, bool)
