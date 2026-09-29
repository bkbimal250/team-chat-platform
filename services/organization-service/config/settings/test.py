import os
from urllib.parse import urlparse

test_database_url = os.environ.get("TEST_DATABASE_URL")
if not test_database_url:
    raise RuntimeError(
        "Organization tests require TEST_DATABASE_URL for an isolated PostgreSQL database."
    )
if "test" not in urlparse(test_database_url).path.lower():
    raise RuntimeError("TEST_DATABASE_URL must target a database whose name contains 'test'.")

os.environ["DATABASE_URL"] = test_database_url
os.environ["SECRET_KEY"] = os.environ.get("TEST_SECRET_KEY", "test-only-not-for-production")
os.environ["ENVIRONMENT"] = "test"
os.environ["RABBITMQ_URL"] = os.environ.get("RABBITMQ_URL", "amqp://unused:unused@localhost/unused")

from .base import *  # noqa: E402, F403

DEV_CONTEXT_ENABLED = True
