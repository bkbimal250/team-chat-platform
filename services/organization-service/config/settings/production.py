import os

from . import base

globals().update({key: getattr(base, key) for key in dir(base) if key.isupper()})
if os.getenv("DEV_CONTEXT_ENABLED", "false").lower() == "true":
    raise RuntimeError("Development identity context is forbidden in production")
DEBUG = False
ENVIRONMENT = os.getenv("ENVIRONMENT", "production")
if ENVIRONMENT == "local":
    raise RuntimeError("Production settings require a non-local ENVIRONMENT")
DEV_CONTEXT_ENABLED = False
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"
