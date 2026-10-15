import os

from django.core.exceptions import ImproperlyConfigured

from . import base

globals().update({key: getattr(base, key) for key in dir(base) if key.isupper()})
JWT_PUBLIC_KEY = os.environ.get("JWT_PUBLIC_KEY", "")
INTERNAL_SERVICE_TOKEN = os.environ.get("INTERNAL_SERVICE_TOKEN", "")
if os.getenv("DEV_CONTEXT_ENABLED", "false").lower() == "true":
    raise RuntimeError("Development identity context is forbidden in production")
DEBUG = False
ENVIRONMENT = os.getenv("ENVIRONMENT", "production")
if ENVIRONMENT == "local":
    raise RuntimeError("Production settings require a non-local ENVIRONMENT")
if not JWT_PUBLIC_KEY or JWT_PUBLIC_KEY.strip() in {"", "replace-with-identity-public-key"}:
    raise ImproperlyConfigured("JWT_PUBLIC_KEY must be configured for production")
if len(INTERNAL_SERVICE_TOKEN) < 32:
    raise ImproperlyConfigured("INTERNAL_SERVICE_TOKEN must be at least 32 characters")
DEV_CONTEXT_ENABLED = False
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_SSL_REDIRECT = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"
