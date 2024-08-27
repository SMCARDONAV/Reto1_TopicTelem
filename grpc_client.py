import grpc
from proto import file_service_pb2
from proto import file_service_pb2_grpc

def run():
    channel = grpc.insecure_channel('localhost:2004')
    stub = file_service_pb2_grpc.FileServiceStub(channel)
    
    response = stub.ListFiles(file_service_pb2.ListFilesRequest())
    print("ListFiles Response:")
    for file_info in response.files:
        print(f"Name: {file_info.name}, URI: {file_info.uri}")

    upload_response = stub.DummyUpload(file_service_pb2.UploadRequest(filename="example.txt"))
    print("DummyUpload Response:", upload_response.message)

    download_response = stub.DummyDownload(file_service_pb2.DownloadRequest(filename="example.txt"))
    print("DummyDownload Response:", download_response.message)

if __name__ == '__main__':
    run()
