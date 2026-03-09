"""Encryption utilities for MAMA CHOL VPN."""
import secrets
import hashlib
import hmac
import base64
from datetime import datetime, timedelta
from typing import Optional, Union, Any
from passlib.context import CryptContext
from jose import JWTError, jwt
from backend.config.settings import settings

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=settings.access_token_expire_minutes))
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.jwt_algorithm)


def create_refresh_token(data: dict) -> str:
    """Create a JWT refresh token."""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=settings.refresh_token_expire_days)
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> Optional[dict]:
    """Decode and validate a JWT token."""
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])
        return payload
    except JWTError:
        return None


def generate_secure_token(length: int = 32) -> str:
    """Generate a cryptographically secure random token."""
    return secrets.token_urlsafe(length)


def generate_vpn_password(length: int = 20) -> str:
    """Generate a strong VPN password."""
    alphabet = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%"
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def generate_subscription_token() -> str:
    """Generate a unique subscription URL token."""
    return secrets.token_urlsafe(24)


def hmac_sign(message: str, key: str) -> str:
    """Create HMAC-SHA256 signature."""
    sig = hmac.new(key.encode(), message.encode(), hashlib.sha256)
    return sig.hexdigest()


def verify_hmac(message: str, signature: str, key: str) -> bool:
    """Verify HMAC-SHA256 signature."""
    expected = hmac_sign(message, key)
    return hmac.compare_digest(expected, signature)


def base64_encode(data: Union[str, bytes]) -> str:
    """Base64 encode data."""
    if isinstance(data, str):
        data = data.encode()
    return base64.b64encode(data).decode()


def base64_decode(data: str) -> bytes:
    """Base64 decode data."""
    return base64.b64decode(data)
