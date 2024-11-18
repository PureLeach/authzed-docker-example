#!/bin/bash
set -e

echo "Waiting for PostgreSQL to be ready..."
/usr/local/bin/wait_for_postgres.sh

echo "Running migrations..."
/usr/local/bin/migrate.sh

echo "Starting SpiceDB..."
exec spicedb serve "$@"
