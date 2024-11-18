from authzed.api.v1.schema_service_pb2 import ReadSchemaRequest
from authzed.api.v1 import AsyncClient

from grpcutil import insecure_bearer_token_credentials



import asyncio


TOKEN = "token"
TARGET = "localhost:50051"
# TARGET = "authzed_spicedb:50051"

async def main():
    client = AsyncClient(target=TARGET, credentials=insecure_bearer_token_credentials(TOKEN))

    request = ReadSchemaRequest()
    response = await client.ReadSchema(request)
    print(f'\033[31m response, { response }, {type(response)} \033[0m')


if __name__ == "__main__":
    asyncio.run(main())