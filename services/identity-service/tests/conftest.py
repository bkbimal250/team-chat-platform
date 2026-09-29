import os

os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://test:test@127.0.0.1/identity_db")
os.environ.setdefault("REDIS_URL", "redis://127.0.0.1:6379/0")
os.environ.setdefault("RABBITMQ_URL", "amqp://test:test@127.0.0.1/%2F")
os.environ.setdefault("ACCESS_TOKEN_PRIVATE_KEY", "test-key")
os.environ.setdefault("ACCESS_TOKEN_PUBLIC_KEY", "test-key")
os.environ.setdefault("SERVICE_AUTH_TOKEN", "test-service-token")
