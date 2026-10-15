import hashlib
import hmac

from app.security.phone import normalize_phone


def phone_digest(phone: str, secret: str) -> str:
    return hmac.new(secret.encode(), normalize_phone(phone).encode(), hashlib.sha256).hexdigest()
