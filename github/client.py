import os
import time
import logging
import requests
import jwt
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class GitHubClient:
    """
    Real GitHub API Client.
    Handles App authentication via JWT -> Installation Token.
    """

    API_BASE = "https://api.github.com"

    def __init__(self, installation_id: Optional[int] = None):
        self.installation_id = installation_id
        self.token = None
        self.headers = {"Accept": "application/vnd.github.v3+json"}

    def authenticate(self, installation_id: int) -> bool:
        """Get an access token for the specific installation."""
        try:
            self.installation_id = installation_id

            # 1. Generate JWT
            private_key = os.getenv("GITHUB_PRIVATE_KEY")
            app_id = os.getenv("GITHUB_APP_ID")

            if not private_key or not app_id:
                logger.error("GITHUB_PRIVATE_KEY or GITHUB_APP_ID missing")
                return False

            # Handle env var newlines
            private_key = private_key.replace("\\n", "\n")

            payload = {
                "iat": int(time.time()),
                "exp": int(time.time()) + 600,  # 10 mins
                "iss": app_id,
            }

            jwt_token = jwt.encode(payload, private_key, algorithm="RS256")

            # 2. Request Installation Token
            jwt_headers = {
                "Authorization": f"Bearer {jwt_token}",
                "Accept": "application/vnd.github.v3+json",
            }

            resp = requests.post(
                f"{self.API_BASE}/app/installations/{installation_id}/access_tokens",
                headers=jwt_headers,
            )
            resp.raise_for_status()

            self.token = resp.json()["token"]
            self.headers["Authorization"] = f"token {self.token}"
            return True

        except Exception as e:
            logger.error(f"GitHub Auth Failed: {e}")
            return False

    def post_comment(self, issue_number: int, body: str, repo_full_name: str) -> None:
        """Post a comment to an issue/PR."""
        if not self.token:
            logger.warning("No token, skipping comment")
            return

        url = f"{self.API_BASE}/repos/{repo_full_name}/issues/{issue_number}/comments"
        try:
            requests.post(url, json={"body": body}, headers=self.headers)
            logger.info(f"Commented on {repo_full_name}#{issue_number}")
        except Exception as e:
            logger.error(f"Failed to comment: {e}")

    def create_pr(
        self, title: str, body: str, head: str, base: str, repo_full_name: str
    ) -> int:
        """Create a Pull Request. Returns PR number."""
        if not self.token:
            logger.error("No token, cannot create PR")
            return 0

        url = f"{self.API_BASE}/repos/{repo_full_name}/pulls"
        payload = {"title": title, "body": body, "head": head, "base": base}

        try:
            resp = requests.post(url, json=payload, headers=self.headers)
            resp.raise_for_status()
            data = resp.json()
            return data["number"]
        except Exception as e:
            logger.error(f"Failed to create PR: {e}")
            if hasattr(e, "response") and e.response:
                logger.error(f"GitHub Response: {e.response.text}")
            raise

    def get_token(self) -> Optional[str]:
        return self.token
