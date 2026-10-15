# User Service runtime processes

Production runs three cooperating processes against the same image:

1. **API** — `uvicorn app.main:app --host 0.0.0.0 --port 8002`
2. **Organization consumer** — `python -m app.consumer_runner` (membership + identity projections)
3. **Outbox publisher** — `python -m app.outbox_runner` (publishes `user.*` domain events)

Apply database migrations before starting any process: `alembic upgrade head`.

Required environment variables are listed in `.env.example`. Staging and production fail fast when secrets or JWT verification keys are missing.
