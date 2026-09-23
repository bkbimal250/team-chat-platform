import os

from . import base

globals().update({key: getattr(base, key) for key in dir(base) if key.isupper()})
DEBUG = os.getenv("DEBUG", "false").lower() == "true"
DEV_CONTEXT_ENABLED = os.getenv("DEV_CONTEXT_ENABLED", "false").lower() == "true"
