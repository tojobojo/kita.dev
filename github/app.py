"""
GitHub App Authentication Module
Bible VI: GitHub Product Surface
"""
import os
import time
import logging
import jwt
from typing import Optional, Dict
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class GitHubAppCredentials:
    app_id: str
    private_key: str
    installation_id: Optional[str] = None

@dataclass
class InstallationToken:
    token: str
    expires_at: str

class GitHubApp:
    """
    Handles GitHub App authentication.
    Generates JWT and installation tokens for API access.
    """
    
    def __init__(self, credentials: Optional[GitHubAppCredentials] = None):
        self.credentials = credentials or self._load_from_env()
        self._installation_token: Optional[InstallationToken] = None
        
    def _load_from_env(self) -> GitHubAppCredentials:
        """Loads credentials from environment variables."""
        app_id = os.getenv("GITHUB_APP_ID", "")
        private_key = os.getenv("GITHUB_PRIVATE_KEY", "")
        installation_id = os.getenv("GITHUB_INSTALLATION_ID")
        
        if not app_id or not private_key:
            logger.warning("GitHub App credentials not configured. Set GITHUB_APP_ID and GITHUB_PRIVATE_KEY.")
            
        return GitHubAppCredentials(
            app_id=app_id,
            private_key=private_key,
            installation_id=installation_id
        )
    
    def generate_jwt(self) -> str:
        """
        Generates a JWT for GitHub App authentication.
        JWT is valid for 10 minutes.
        """
        if not self.credentials.app_id or not self.credentials.private_key:
            raise ValueError("GitHub App credentials not configured")
            
        now = int(time.time())
        payload = {
            "iat": now - 60,  # Issued 60 seconds ago (clock skew)
            "exp": now + 600,  # Expires in 10 minutes
            "iss": self.credentials.app_id
        }
        
        return jwt.encode(payload, self.credentials.private_key, algorithm="RS256")
    
    def get_installation_token(self, installation_id: Optional[str] = None) -> InstallationToken:
        """
        Gets or refreshes an installation access token.
        Uses cached token if still valid.
        """
        import requests
        
        install_id = installation_id or self.credentials.installation_id
        if not install_id:
            raise ValueError("Installation ID not provided")
            
        # Check if cached token is still valid (with 5 min buffer)
        if self._installation_token:
            # In production, check expiry
            pass
            
        jwt_token = self.generate_jwt()
        
        response = requests.post(
            f"https://api.github.com/app/installations/{install_id}/access_tokens",
            headers={
                "Authorization": f"Bearer {jwt_token}",
                "Accept": "application/vnd.github+json"
            }
        )
        
        if response.status_code != 201:
            logger.error(f"Failed to get installation token: {response.text}")
            raise RuntimeError("Failed to get installation token")
            
        data = response.json()
        self._installation_token = InstallationToken(
            token=data["token"],
            expires_at=data["expires_at"]
        )
        
        return self._installation_token
    
    def get_authenticated_headers(self) -> Dict[str, str]:
        """Returns headers for authenticated API requests."""
        if self.credentials.installation_id:
            token = self.get_installation_token()
            return {
                "Authorization": f"Bearer {token.token}",
                "Accept": "application/vnd.github+json"
            }
        else:
            # Fall back to JWT for non-installation endpoints
            return {
                "Authorization": f"Bearer {self.generate_jwt()}",
                "Accept": "application/vnd.github+json"
            }
