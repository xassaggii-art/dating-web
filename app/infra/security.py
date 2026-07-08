import base64
import hashlib
import secrets
from datetime import UTC, datetime, timedelta
from uuid import UUID

import pyotp
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from cryptography.fernet import Fernet, InvalidToken
from jose import JWTError, jwt

from app.config import get_settings

_ph = PasswordHasher()


def hash_password(password: str) -> str:
    return _ph.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return _ph.verify(hashed, plain)
    except VerifyMismatchError:
        return False


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def generate_refresh_token() -> str:
    return secrets.token_urlsafe(48)


def create_access_token(user_id: UUID, session_id: UUID) -> str:
    settings = get_settings()
    expire = datetime.now(UTC) + timedelta(minutes=settings.access_token_expire_minutes)
    payload = {
        "sub": str(user_id),
        "sid": str(session_id),
        "type": "access",
        "exp": expire,
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> tuple[UUID, UUID] | None:
    settings = get_settings()
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        if payload.get("type") != "access":
            return None
        return UUID(payload["sub"]), UUID(payload["sid"])
    except (JWTError, KeyError, ValueError):
        return None


def _fernet() -> Fernet:
    settings = get_settings()
    key = base64.urlsafe_b64encode(hashlib.sha256(settings.encryption_key.encode()).digest())
    return Fernet(key)


def encrypt_secret(value: str) -> str:
    return _fernet().encrypt(value.encode()).decode()


def decrypt_secret(value: str) -> str | None:
    try:
        return _fernet().decrypt(value.encode()).decode()
    except InvalidToken:
        return None


def generate_totp_secret() -> str:
    return pyotp.random_base32()


def verify_totp(secret: str, code: str) -> bool:
    totp = pyotp.TOTP(secret)
    return totp.verify(code, valid_window=1)


def get_totp_provisioning_uri(secret: str, email: str) -> str:
    settings = get_settings()
    totp = pyotp.TOTP(secret)
    return totp.provisioning_uri(name=email, issuer_name=settings.app_name)
