import grpc

from proto import node_service_pb2, node_service_pb2_grpc


def run():
    channel = grpc.insecure_channel('localhost:3000')
    stub = node_service_pb2_grpc.NodeServiceStub(channel)
    address = node_service_pb2.Address(ip='127.0.0.1', port=2000)
    response = stub.JoinNetwork(address)
    print(response)


if __name__ == '__main__':
    run()
