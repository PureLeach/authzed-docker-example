import grpc
from authzed.api.v1.schema_service_pb2_grpc import SchemaServiceStub
from authzed.api.v1.schema_service_pb2 import ReadSchemaRequest
from grpcutil import bearer_token_credentials, insecure_bearer_token_credentials
from authzed.api.v1 import SyncClient

# Указываем адрес и порт сервера
channel = grpc.insecure_channel('localhost:50051')

# Указываем токен
token = "token"
metadata = [('authorization', f'Bearer {token}')]

# Создаем клиента для получения схемы
schema_stub = SchemaServiceStub(channel)

def get_schema():
    # Используем ReadSchema для запроса схемы
    request = ReadSchemaRequest()
    response = schema_stub.ReadSchema(request, metadata=metadata)
    print(f'\033[31m response, { response }, {type(response)} \033[0m')


def check_client():
    client = SyncClient(target='localhost:50051', credentials=insecure_bearer_token_credentials(token))
    print(f'\033[31m client, { client }, {type(client)} \033[0m')
    
    request = ReadSchemaRequest()
    response = client.ReadSchema(request)
    print(f'\033[31m response, { response }, {type(response)} \033[0m')



if __name__ == '__main__':
    get_schema()
    # check_client()


