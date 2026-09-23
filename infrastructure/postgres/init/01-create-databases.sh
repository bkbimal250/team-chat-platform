#!/bin/sh
set -eu
for db in teamchat_organization_db teamchat_identity_db teamchat_user_db teamchat_conversation_db teamchat_message_db teamchat_media_db teamchat_notification_db; do
  psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname postgres <<SQL
SELECT 'CREATE DATABASE $db' WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = '$db')\gexec
SQL
done
