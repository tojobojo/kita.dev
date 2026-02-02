import re
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)


class DetectedSecret:
    def __init__(self, secret_type: str, redacted_value: str, context: str):
        self.secret_type = secret_type
        self.redacted_value = redacted_value
        self.context = context

    def __repr__(self):
        return f"<DetectedSecret type={self.secret_type}>"


class SecretDetector:
    """
    Scans text for secrets using regex patterns.
    Bible V, Section 9: Secrets Handling
    """

    # Regex patterns for common secrets
    PATTERNS = {
        "AWS Access Key": r"AKIA[0-9A-Z]{16}",
        "AWS Secret Key": r"(?i)aws_secret_access_key[ =]+[a-zA-Z0-9/+]{40}",
        "GitHub Token": r"(gh[pous]_[a-zA-Z0-9]{36,})",
        "Generic Private Key": r"-----BEGIN (RSA|DSA|EC|OPENSSH|PRIVATE) KEY-----",
        "Slack Token": r"xox[baprs]-([0-9a-zA-Z]{10,48})",
    }

    @staticmethod
    def scan(text: str, context_window: int = 20) -> List[DetectedSecret]:
        """
        Scans text for secrets. Returns a list of detected secrets.
        Values are redacted in the return object.
        """
        detected = []

        for name, pattern in SecretDetector.PATTERNS.items():
            matches = re.finditer(pattern, text)
            for match in matches:
                start, end = match.span()
                matched_text = match.group(0)

                # Redact: keep first 2 chars, mask rest
                if len(matched_text) > 4:
                    redacted = matched_text[:2] + "*" * (len(matched_text) - 2)
                else:
                    redacted = "****"

                # Capture context
                ctx_start = max(0, start - context_window)
                ctx_end = min(len(text), end + context_window)
                context = text[ctx_start:ctx_end]

                logger.critical(
                    f"SECURITY: Secret detected! Type: {name} | Location: indices {start}-{end}"
                )

                detected.append(DetectedSecret(name, redacted, context))

        return detected

    @staticmethod
    def validate_content_safe(text: str) -> None:
        """
        Raises generic SecurityError if secrets are found.
        This is a helper for fast fail.
        """
        issues = SecretDetector.scan(text)
        if issues:
            raise SecurityError(
                f"Found {len(issues)} secrets in content. Types: {[i.secret_type for i in issues]}"
            )


class SecurityError(Exception):
    pass
