"""Tests for authentication module."""

import unittest
from src.auth import validate_email, create_user, hash_password, authenticate


class TestAuth(unittest.TestCase):

    def test_validate_email_valid(self):
        self.assertTrue(validate_email("user@example.com"))
        self.assertTrue(validate_email("test.user@domain.org"))

    def test_validate_email_invalid(self):
        self.assertFalse(validate_email(""))
        self.assertFalse(validate_email("invalid"))
        self.assertFalse(validate_email("no@tld"))

    def test_hash_password(self):
        hash1 = hash_password("password123")
        hash2 = hash_password("password123")
        self.assertEqual(hash1, hash2)

        hash3 = hash_password("different")
        self.assertNotEqual(hash1, hash3)

    def test_create_user(self):
        user = create_user("test@example.com", "password")
        self.assertIsNotNone(user)
        self.assertEqual(user.email, "test@example.com")

    def test_create_user_invalid_email(self):
        user = create_user("invalid", "password")
        self.assertIsNone(user)

    def test_authenticate(self):
        success, token = authenticate("user@example.com", "password")
        self.assertTrue(success)
        self.assertIsNotNone(token)

    # TODO: Add token expiration tests
    # TODO: Add password reset tests


if __name__ == "__main__":
    unittest.main()
