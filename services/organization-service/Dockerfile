FROM python:3.12-slim AS builder
COPY --from=ghcr.io/astral-sh/uv:0.12.17 /uv /usr/local/bin/uv
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project --no-editable

FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PATH="/app/.venv/bin:$PATH"
RUN groupadd --system organization && useradd --system --gid organization organization
WORKDIR /app
COPY --from=builder /app/.venv /app/.venv
COPY --chown=organization:organization . .
RUN SECRET_KEY=build-only-placeholder DATABASE_URL=postgresql://unused:unused@localhost/unused RABBITMQ_URL=amqp://unused:unused@localhost/unused python manage.py collectstatic --noinput
USER organization
EXPOSE 8000
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "2", "--timeout", "30", "--access-logfile", "-"]
