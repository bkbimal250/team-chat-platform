# Notification Service operations

## API

`uvicorn app.main:app --host 0.0.0.0 --port 8006`

Production requires external PostgreSQL, `JWT_PUBLIC_KEY`, `RABBITMQ_URL`, `INTERNAL_SERVICE_TOKEN`, and `PUSH_PROVIDER=fcm` with `FIREBASE_CREDENTIALS_JSON`.

## Rabbit consumer

`python -m app.consumer_runner`

Queues: `notification.projections`, `notification.message-created`, `notification.org-events`.

## Delivery worker

`python -m app.delivery_worker`

Claims `notification_deliveries` and sends via FCM (or fake provider in development).

## Outbox publisher

`python -m app.outbox_runner`

Publishes `notification.*` events to `notification.events`.
