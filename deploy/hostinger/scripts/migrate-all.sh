#!/usr/bin/env sh
# Run once after Postgres is healthy and before or during first app start.
set -eu
cd "$(dirname "$0")/.."
COMPOSE="docker compose --env-file .env -f docker-compose.yml"

echo "==> Organization (Django)"
$COMPOSE run --rm organization-service python manage.py migrate --noinput

for svc_db in \
  "identity-service:teamchat_identity_db" \
  "user-service:teamchat_user_db" \
  "conversation-service:teamchat_conversation_db" \
  "messaging-service:teamchat_message_db" \
  "media-service:teamchat_media_db" \
  "notification-api:teamchat_notification_db"
do
  svc="${svc_db%%:*}"
  echo "==> $svc (Alembic)"
  $COMPOSE run --rm "$svc" python -m alembic upgrade head
done

echo "Migrations finished. Confirm identity revision includes 0011_device_e2ee_keys and messaging 0005_message_e2ee_envelope."
