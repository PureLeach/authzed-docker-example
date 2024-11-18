#!/bin/sh

set -e

until PGPASSWORD="$POSTGRES_PASSWORD" psql -h $POSTGRES_HOST -U $POSTGRES_USER -d $SPICEDB_POSTGRES_DB -c "select 1" > /dev/null 2>&1; do
  echo "Postgres is unavailable - sleeping"
  sleep 1
done


>&2 echo "Postgres is up - executing command"
exec "$@"
