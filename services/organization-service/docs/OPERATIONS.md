# Organization Service processes

Run migrations before any process: `python manage.py migrate --noinput`.

## API (HTTP)

`gunicorn config.wsgi:application --bind 0.0.0.0:8000`

## Outbox publisher (required)

`python manage.py publish_outbox` (loop) or `python manage.py publish_outbox --once`

Publishes committed `OutboxEvent` rows to RabbitMQ exchange `organization.events`.

## Configuration

See `services/organization-service/.env.example`. Production (`config.settings.production`) requires non-local `ENVIRONMENT`, configured `JWT_PUBLIC_KEY`, and `INTERNAL_SERVICE_TOKEN` of at least 32 characters.
