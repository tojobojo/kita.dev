import unittest
import tempfile
from unittest.mock import patch, MagicMock
from sandbox.limits import ResourceLimits
from guardrails.secrets import SecretDetector, SecurityError
from guardrails.rules import is_command_allowed
from sandbox.executor import SandboxExecutor, SecurityViolation


class TestSecurity(unittest.TestCase):

    # --- Guardrails: Rules ---
    def test_allowed_commands(self):
        self.assertTrue(is_command_allowed("python main.py"))
        self.assertTrue(is_command_allowed("npm install"))
        self.assertTrue(is_command_allowed("grep 'foo' bar.txt"))

    def test_forbidden_commands(self):
        self.assertFalse(is_command_allowed("curl malicious.site"))
        self.assertFalse(is_command_allowed("wget malicious.site"))
        self.assertFalse(
            is_command_allowed("rm -rf / && echo 'oops'")
        )  # Chaining blocked
        self.assertFalse(
            is_command_allowed("python script.py | grep foo")
        )  # Pipe blocked
        self.assertFalse(is_command_allowed("sudo rm -rf"))

    # --- Guardrails: Secrets ---
    def test_secret_detection_aws(self):
        text = "My key is AKIA1234567890123456"
        secrets = SecretDetector.scan(text)
        self.assertEqual(len(secrets), 1)
        self.assertEqual(secrets[0].secret_type, "AWS Access Key")
        self.assertTrue("AK" in secrets[0].redacted_value)
        self.assertFalse(
            "AKIA" in secrets[0].redacted_value
        )  # Should ensure IA is masked

    def test_secret_detection_helper(self):
        with self.assertRaises(SecurityError):
            SecretDetector.validate_content_safe("AKIA1234567890123456")

    # --- Sandbox: Limits ---
    def test_limits_validation(self):
        safe_limits = ResourceLimits(cpu_seconds=60, timeout_seconds=100)
        safe_limits.validate()  # Should not raise

        unsafe_limits = ResourceLimits(timeout_seconds=99999)
        with self.assertRaises(ValueError):
            unsafe_limits.validate()

    # --- Sandbox: Executor ---
    @patch("sandbox.docker_utils.ensure_sandbox_image")
    @patch("subprocess.run")
    def test_sandbox_run_success(self, mock_run, mock_ensure_image):
        mock_run.return_value = MagicMock(returncode=0, stdout="hello", stderr="")

        executor = SandboxExecutor()
        with tempfile.TemporaryDirectory() as tmpdir:
            result = executor.run("echo hello", tmpdir)

        self.assertEqual(result.exit_code, 0)
        self.assertEqual(result.stdout, "hello")

        # Verify docker command structure
        args, kwargs = mock_run.call_args
        cmd_list = args[0]
        self.assertEqual(cmd_list[0], "docker")
        self.assertIn("--network", cmd_list)
        self.assertIn("none", cmd_list)
        self.assertIn("--read-only", cmd_list)

    def test_sandbox_run_blocked(self):
        executor = SandboxExecutor()
        with tempfile.TemporaryDirectory() as tmpdir:
            with self.assertRaises(SecurityViolation):
                executor.run("curl google.com", tmpdir)

    @patch("sandbox.docker_utils.ensure_sandbox_image")
    @patch("subprocess.run")
    def test_sandbox_output_redaction(self, mock_run, mock_ensure_image):
        # Simulate command returning a secret
        mock_run.return_value = MagicMock(
            returncode=0, stdout="KEY=AKIA1234567890123456", stderr=""
        )

        executor = SandboxExecutor()
        with tempfile.TemporaryDirectory() as tmpdir:
            result = executor.run("echo safe_command_but_unsafe_output", tmpdir)

        self.assertEqual(result.exit_code, -2)  # Security violation code
        self.assertIn("REDACTED", result.stdout)


if __name__ == "__main__":
    unittest.main()
