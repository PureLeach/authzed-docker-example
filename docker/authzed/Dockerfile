FROM authzed/spicedb:v1.32.0-amd64 as spicedb

FROM authzed/zed:v0.18.1-amd64 as zed

FROM debian:11-slim AS main


COPY --from=spicedb /usr/local/bin/spicedb /usr/local/bin/spicedb

COPY --from=zed /usr/local/bin/zed /usr/local/bin/zed

RUN apt-get update && apt-get install -y curl gnupg1 && \
    apt-get update && \
    apt-get install -y netcat && \
    apt-get install --no-install-recommends -y -o Acquire::Retries=3 \
    postgresql-client

COPY entrypoint.sh /usr/local/bin/

RUN chmod +x /usr/local/bin/entrypoint.sh

COPY schema.yaml /etc/schema.yaml

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
