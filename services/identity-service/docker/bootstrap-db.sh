#!/bin/sh
set -eu
export PGPASSWORD="$POSTGRES_PASSWORD"
if ! psql -h postgres -U organization_migrator -d postgres -tAc "SELECT 1 FROM pg_database WHERE datname = 'identity_db'" | grep -q 1; then
  psql -h postgres -U organization_migrator -d postgres -c "CREATE ROLE identity_app LOGIN PASSWORD '$DB_PASSWORD'"
  psql -h postgres -U organization_migrator -d postgres -c "CREATE DATABASE identity_db OWNER identity_app"
fi
