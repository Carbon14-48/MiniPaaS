from src.services.auth_service import validate_password, hash_password, verify_password


class TestPasswordValidation:
    def test_valid_password(self):
        valid, msg = validate_password("Password123")
        assert valid is True
        assert msg == ""

    def test_short_password(self):
        valid, msg = validate_password("Pass1")
        assert valid is False
        assert "at least 8 characters" in msg

    def test_no_uppercase(self):
        valid, msg = validate_password("password123")
        assert valid is False
        assert "uppercase" in msg.lower()

    def test_no_lowercase(self):
        valid, msg = validate_password("PASSWORD123")
        assert valid is False
        assert "lowercase" in msg.lower()

    def test_no_digit(self):
        valid, msg = validate_password("PasswordABC")
        assert valid is False
        assert "digit" in msg.lower()


class TestPasswordHashing:
    def test_hash_password(self):
        password = "Password123"
        hashed = hash_password(password)
        assert hashed != password
        assert len(hashed) > 0

    def test_verify_password_correct(self):
        password = "Password123"
        hashed = hash_password(password)
        assert verify_password(password, hashed) is True

    def test_verify_password_incorrect(self):
        password = "Password123"
        hashed = hash_password(password)
        assert verify_password("WrongPassword123", hashed) is False
