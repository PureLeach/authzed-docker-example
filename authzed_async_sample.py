import asyncio
import os

from authzed.api.v1.schema_service_pb2 import ReadSchemaRequest
from authzed.api.v1 import AsyncClient
from grpcutil import insecure_bearer_token_credentials


HOST = "localhost"
PORT = os.getenv("SPICEDB_GRPC_ADDR", default="50051")
TOKEN = os.getenv("SPICEDB_GRPC_PRESHARED_KEY", default="token")


async def read_schema_request(client):
    request = ReadSchemaRequest()
    response = await client.ReadSchema(request)
    print(response)


async def main():
    client = AsyncClient(
        target=f"{HOST}:{PORT}", credentials=insecure_bearer_token_credentials(TOKEN)
    )
    await read_schema_request(client)


if __name__ == "__main__":
    asyncio.run(main())
