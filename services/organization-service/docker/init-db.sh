#!/bin/sh
set -eu
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" --set=app_password="$APP_PASSWORD" <<'SQL'
CREATE ROLE organization_app LOGIN PASSWORD :'app_password';
GRANT CONNECT ON DATABASE organization_db TO organization_app;
GRANT USAGE ON SCHEMA public TO organization_app;
ALTER DEFAULT PRIVILEGES FOR ROLE organization_migrator IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO organization_app;
ALTER DEFAULT PRIVILEGES FOR ROLE organization_migrator IN SCHEMA public GRANT USAGE, SELECT ON SEQUENCES TO organization_app;
SQL
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" --set=app_password="$APP_PASSWORD" <<'SQL'
CREATE ROLE identity_app LOGIN PASSWORD :'app_password';
CREATE DATABASE identity_db OWNER identity_app;
SQL
