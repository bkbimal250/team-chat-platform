"""Bounded local event archive for inspecting real domain publications."""

import os

import pika

url = os.environ["RABBITMQ_URL"]
if "127.0.0.1:5672/" not in url or os.environ.get("APP_ENV") != "development":
    raise RuntimeError("Local broker only")
connection = pika.BlockingConnection(pika.URLParameters(url))
channel = connection.channel()
channel.queue_declare(
    "local.events.audit", durable=True, arguments={"x-max-length": 1000}
)
for exchange in [
    "organization.events",
    "user.events",
    "messaging.events",
    "media.events",
    "notification.events",
]:
    channel.exchange_declare(exchange, "topic", durable=True)
    channel.queue_bind("local.events.audit", exchange, "#")
connection.close()
print("Bounded local event archive ready; application queues unchanged")
