#!/bin/bash


set -e


echo "Running migrations..."
spicedb datastore migrate head \
    --skip-release-check=true \
    --datastore-engine postgres \
    --datastore-conn-uri "postgres://${POSTGRES_USER}:${POSTGRES_PASSWORD}@${POSTGRES_HOST}/${SPICEDB_POSTGRES_DB}"


echo "Validating schema..."
zed --endpoint "${AUTHZED_HOST}:${SPICEDB_GRPC_ADDR}" \
    --token "${SPICEDB_GRPC_PRESHARED_KEY}" \
    --no-verify-ca --insecure --skip-version-check=true validate /etc/schema.yaml


echo "Starting SpiceDB in the background..."
spicedb "$@" &


echo "Waiting for SpiceDB to become ready..."
until nc -z "${AUTHZED_HOST}" "${SPICEDB_GRPC_ADDR}"; do
    echo "SpiceDB is not ready yet, retrying..."
    sleep 1
done


echo "Importing schema..."
zed --endpoint "${AUTHZED_HOST}:${SPICEDB_GRPC_ADDR}" \
    --token "${SPICEDB_GRPC_PRESHARED_KEY}" \
    --no-verify-ca --insecure --skip-version-check=true import /etc/schema.yaml


wait
