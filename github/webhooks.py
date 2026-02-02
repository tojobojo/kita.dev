"""
GitHub Webhook Handlers
Bible VI: GitHub Product Surface
"""

import os
import hmac
import hashlib
import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class WebhookEvent:
    event_type: str
    action: Optional[str]
    payload: Dict[str, Any]
    delivery_id: str
    signature: Optional[str] = None


class WebhookVerifier:
    """
    Verifies incoming GitHub webhook signatures.
    """

    def __init__(self, secret: Optional[str] = None):
        self.secret = secret or os.getenv("GITHUB_WEBHOOK_SECRET", "")

    def verify(self, payload_body: bytes, signature_header: str) -> bool:
        """
        Verifies webhook signature using HMAC-SHA256.
        Returns True if signature is valid.
        """
        if not self.secret:
            logger.warning("Webhook secret not configured. Skipping verification.")
            return True  # Allow in dev, but log warning

        if not signature_header:
            logger.error("Missing X-Hub-Signature-256 header")
            return False

        # GitHub sends: sha256=<hash>
        expected_signature = (
            "sha256="
            + hmac.new(
                self.secret.encode("utf-8"), payload_body, hashlib.sha256
            ).hexdigest()
        )

        return hmac.compare_digest(signature_header, expected_signature)


class WebhookRouter:
    """
    Routes webhook events to appropriate handlers.
    Bible VI, Section 1: Supported entry points.
    """

    # Bible VI, Section 1: Supported events
    SUPPORTED_EVENTS = {
        "issue_comment": ["created"],
        "issues": ["opened", "edited"],
        "pull_request_review_comment": ["created"],
    }

    def is_supported(self, event: WebhookEvent) -> bool:
        """Checks if event type and action are supported."""
        if event.event_type not in self.SUPPORTED_EVENTS:
            return False
        allowed_actions = self.SUPPORTED_EVENTS[event.event_type]
        return event.action in allowed_actions

    def parse_event(
        self, headers: Dict[str, str], payload: Dict[str, Any]
    ) -> WebhookEvent:
        """Parses raw webhook data into WebhookEvent."""
        return WebhookEvent(
            event_type=headers.get("X-GitHub-Event", ""),
            action=payload.get("action"),
            payload=payload,
            delivery_id=headers.get("X-GitHub-Delivery", ""),
            signature=headers.get("X-Hub-Signature-256"),
        )

    def extract_context(self, event: WebhookEvent) -> Dict[str, Any]:
        """
        Extracts relevant context from webhook payload.
        Returns normalized context for agent processing.
        """
        payload = event.payload

        context = {
            "event_type": event.event_type,
            "action": event.action,
            "repository": {
                "full_name": payload.get("repository", {}).get("full_name", ""),
                "clone_url": payload.get("repository", {}).get("clone_url", ""),
                "default_branch": payload.get("repository", {}).get(
                    "default_branch", "main"
                ),
            },
            "sender": payload.get("sender", {}).get("login", ""),
        }

        # Extract issue context
        if "issue" in payload:
            issue = payload["issue"]
            context["issue"] = {
                "number": issue.get("number"),
                "title": issue.get("title", ""),
                "body": issue.get("body", ""),
                "labels": [l.get("name") for l in issue.get("labels", [])],
            }

        # Extract comment context
        if "comment" in payload:
            context["comment"] = {
                "body": payload["comment"].get("body", ""),
                "user": payload["comment"].get("user", {}).get("login", ""),
            }

        # Extract PR context if present
        if "pull_request" in payload:
            pr = payload["pull_request"]
            context["pull_request"] = {
                "number": pr.get("number"),
                "title": pr.get("title", ""),
                "head_branch": pr.get("head", {}).get("ref", ""),
                "base_branch": pr.get("base", {}).get("ref", ""),
            }

        return context
