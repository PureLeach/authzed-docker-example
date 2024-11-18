#!/bin/bash

spicedb migrate head --skip-release-check=true --datastore-engine postgres --datastore-conn-uri postgres://${POSTGRES_USER}:${POSTGRES_PASSWORD}@${POSTGRES_HOST}/${SPICEDB_POSTGRES_DB}


echo "Waiting for gRPC server to be ready..."
until nc -z ${AUTHZED_HOST} ${AUTHZED_GRPC_PORT}; do
    sleep 1
done


echo "Validating schema..."
zed --endpoint ${AUTHZED_HOST}:${AUTHZED_GRPC_PORT} --token ${AUTHZED_TOKEN} --no-verify-ca --insecure --skip-version-check=true validate /etc/schema.yaml


if [ $? -eq 0 ]; then
    echo "Schema is valid. Importing schema..."
    zed --endpoint ${AUTHZED_HOST}:${AUTHZED_GRPC_PORT} --token ${AUTHZED_TOKEN} --no-verify-ca --skip-version-check=true import /etc/schema.yaml
else
    echo "Schema validation failed. Fix the errors before importing."
    exit 1
fi
