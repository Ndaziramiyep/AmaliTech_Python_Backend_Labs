#!/bin/bash
# Runs once, only against a fresh (empty) data volume — the official Postgres
# image auto-creates $POSTGRES_DB (the "postgres" maintenance db here) but
# nothing else, so the three services' actual databases are created here.
set -e

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    CREATE DATABASE auth_service;
    CREATE DATABASE url_service;
    CREATE DATABASE analytics_service;
EOSQL
