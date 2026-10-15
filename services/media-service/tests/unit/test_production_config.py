import pytest
from pydantic import ValidationError

from app.config import MediaSettings


def test_production_requires_internal_auth_configuration():
    with pytest.raises(ValidationError, match="INTERNAL_SERVICE_TOKEN"):
        MediaSettings(
            app_env="production",
            media_storage_backend="s3",
            aws_region="ap-south-1",
            media_s3_bucket="private",
            jwt_public_key="key",
            database_url="postgresql+asyncpg://media:pw@db.internal/media",
        )
