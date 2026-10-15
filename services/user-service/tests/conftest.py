import os

os.environ.setdefault(
    "DATABASE_URL", "postgresql+asyncpg://test:test@127.0.0.1/teamchat_user_db"
)
os.environ.setdefault("INTERNAL_SERVICE_TOKEN", "test-internal-service-token-32chars!!")
os.environ.setdefault("IDENTITY_JWT_PUBLIC_KEY", "test-key")
os.environ.setdefault("ACCESS_TOKEN_PRIVATE_KEY", "test-key")
os.environ.setdefault("IDENTITY_JWT_ISSUER", "identity-service")
os.environ.setdefault("REDIS_URL", "redis://127.0.0.1:6379/0")
os.environ.setdefault("RABBITMQ_URL", "amqp://guest:guest@127.0.0.1:5672/")
