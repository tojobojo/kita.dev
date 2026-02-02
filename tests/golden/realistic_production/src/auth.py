"""
Realistic Production Golden Repository - Authentication Module
Simulates a production authentication system with intentional issues.
"""

import hashlib
import time
from typing import Optional, Dict, Tuple
from dataclasses import dataclass

# Simulated token store
_token_store: Dict[str, dict] = {}


@dataclass
class User:
    id: int
    email: str
    password_hash: str
    created_at: float


def hash_password(password: str) -> str:
    """Hash a password using SHA-256."""
    return hashlib.sha256(password.encode()).hexdigest()


def validate_email(email: str) -> bool:
    """Validate email format.

    Note: This logic could be extracted to a separate module.
    """
    if not email:
        return False
    if "@" not in email:
        return False
    if "." not in email.split("@")[1]:
        return False
    if len(email) > 254:
        return False
    return True


def create_user(email: str, password: str) -> Optional[User]:
    """Create a new user."""
    if not validate_email(email):
        return None

    return User(
        id=int(time.time() * 1000),
        email=email,
        password_hash=hash_password(password),
        created_at=time.time(),
    )


def generate_token(user: User) -> str:
    """Generate an authentication token.

    BUG: Token never expires - should have expiration.
    TODO: Add token expiration.
    """
    token = hashlib.sha256(f"{user.id}:{time.time()}".encode()).hexdigest()
    _token_store[token] = {
        "user_id": user.id,
        "created_at": time.time(),
        # Missing: expires_at
    }
    return token


def verify_token(token: str) -> Optional[int]:
    """Verify a token and return user_id if valid.

    BUG: Doesn't check expiration.
    """
    if token not in _token_store:
        return None

    token_data = _token_store[token]
    # BUG: Should check if token is expired
    return token_data["user_id"]


def authenticate(email: str, password: str) -> Tuple[bool, Optional[str]]:
    """Authenticate a user and return a token."""
    # Simplified for testing - would normally check database
    if not validate_email(email):
        return False, None

    # Mock authentication
    user = create_user(email, password)
    if user:
        token = generate_token(user)
        return True, token

    return False, None


# TODO: Add password reset functionality
