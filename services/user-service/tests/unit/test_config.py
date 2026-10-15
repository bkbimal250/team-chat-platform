import pytest
from pydantic import ValidationError

from app.config import Settings, reset_settings


def test_production_requires_strong_internal_token():
    with pytest.raises(ValidationError, match="INTERNAL_SERVICE_TOKEN"):
        Settings(
            _env_file=None,
            APP_ENV="production",
            DATABASE_URL="postgresql+asyncpg://user:pass@postgres:5432/db",
            INTERNAL_SERVICE_TOKEN="short",
            IDENTITY_JWT_PUBLIC_KEY="production-public-key-material",
        )
    reset_settings()
