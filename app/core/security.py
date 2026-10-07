from datetime import datetime, timedelta, timezone
from uuid import UUID
import hashlib
import secrets

from jose import JWTError, jwt
from pwdlib import PasswordHash

from app.core.config import settings


password_hash = PasswordHash.recommended()


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(password: str, hashed_password: str) -> bool:
    return password_hash.verify(password, hashed_password)


def create_access_token(user_id: UUID) -> str:
    expires_at = datetime.now(timezone.utc) + timedelta(
        minutes=settings.access_token_expire_minutes
    )

    payload = {
        "sub": str(user_id),
        "type": "access",
        "exp": expires_at,
    }

    return jwt.encode(
        payload,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )


def decode_access_token(token: str) -> UUID:
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
    except JWTError as exc:
        raise ValueError("Invalid access token") from exc

    if payload.get("type") != "access":
        raise ValueError("Invalid token type")

    subject = payload.get("sub")

    if not subject:
        raise ValueError("Token subject is missing")

    try:
        return UUID(subject)
    except ValueError as exc:
        raise ValueError("Invalid user ID in token") from exc

def generate_qr_token() -> str:
    return secrets.token_urlsafe(32)


def hash_qr_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()