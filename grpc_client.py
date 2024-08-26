import grpc
from proto import file_service_pb2
from proto import file_service_pb2_grpc

def run():
    # Dirección del servidor gRPC
    channel = grpc.insecure_channel('localhost:2001')
    
    # Crear un stub (cliente) del servicio gRPC
    stub = file_service_pb2_grpc.FileServiceStub(channel)
    
    # Ejemplo de llamada al método ListFiles
    response = stub.ListFiles(file_service_pb2.ListFilesRequest())
    
    print("ListFiles Response:")
    for file_info in response.files:
        print(f"Name: {file_info.name}, URI: {file_info.uri}")
    
    # Ejemplo de llamada al método DummyUpload
    upload_response = stub.DummyUpload(file_service_pb2.UploadRequest(filename="example.txt"))
    print("DummyUpload Response:", upload_response.message)

    # Ejemplo de llamada al método DummyDownload
    download_response = stub.DummyDownload(file_service_pb2.DownloadRequest(filename="example.txt"))
    print("DummyDownload Response:", download_response.message)

if __name__ == '__main__':
    run()
