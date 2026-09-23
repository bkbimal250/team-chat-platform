import hashlib
import hmac
import secrets

from argon2 import PasswordHasher

hasher = PasswordHasher()


def new_secret(bytes_: int = 32) -> str:
    return secrets.token_urlsafe(bytes_)


def hash_secret(value: str) -> str:
    return hasher.hash(value)


def verify_secret(value: str, hashed: str) -> bool:
    try:
        return hasher.verify(hashed, value)
    except Exception:
        return False


def opaque_token() -> str:
    return new_secret(48)


def token_hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def equal_digest(left: str, right: str) -> bool:
    return hmac.compare_digest(left, right)
