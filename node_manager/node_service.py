
from collections import OrderedDict
from concurrent import futures
import time

import grpc
from node_manager.hash import getHash
from proto import file_service_pb2, file_service_pb2_grpc, node_service_pb2, node_service_pb2_grpc

myNode = None
MAX_BITS = 10
MAX_NODES = 2 ** MAX_BITS


def create_node(ip, grpc_port, directory=None, seed_url=None):
    global myNode
    myNode = Node(ip, grpc_port, directory, seed_url)
    return myNode


class FileServicer(file_service_pb2_grpc.FileServiceServicer):
    def __init__(self, node):
        self.node = node

    def ListFiles(self, request, context):
        files = [
            file_service_pb2.FileInfo(
                name=filename,
                uri=f"http://{self.node.ip}:{self.node.port}/files/{filename}"
            )
            for filename in os.listdir(self.node.directory)
            if os.path.isfile(os.path.join(self.node.directory, filename))
        ]
        return file_service_pb2.ListFilesResponse(files=files)
    
    def DummyDownload(self, request, context):
        return file_service_pb2.DownloadResponse(message=f"Dummy download of {request.filename}")

    def DummyUpload(self, request, context):
        return file_service_pb2.UploadResponse(message=f"Dummy upload of {request.filename}")


class Node_service(node_service_pb2_grpc.NodeServiceServicer):
    def __init__(self, node):
        self.node = node
           
    def JoinNetwork(self, request):
        try:            
            ip = request.ip
            port = request.port
            message = self.node.sendJoinRequest(ip, port)
            return message
        except Exception as e:
            print(f"Error occurred: {e}")
            return {"error": "An unexpected error occurred."}, 500
        
    def LookUpID(self, request):
        return self.node.lookupID(request.id)
    
    def ConnectPeer(self, request, context):
        address = request
        print("Connection with:", address[0], ":", address[1])
        print("Join network request received")
        return self.node.joinNode(address)
    
    def LeaveNetwork(self, request, context):
        return self.node.leaveNetwork()
    
    def GetFingerTable(self, request, context):
        return self.node.printFTable()
    
    def GetPredSucc(self, request, context):
        return {"My ID": self.node.id, "Predecessor": self.node.predID, "Successor": self.node.succID}
        

class Node:
    def __init__(self, ip, port, directory=None, seed_url=None):
        self.filenameList = []
        self.ip = ip
        self.port = port
        self.directory = directory
        self.address = (ip, port)
        self.id = getHash(ip + ":" + str(port))
        self.pred = (ip, port)
        self.predID = self.id
        self.succ = (ip, port)
        self.succID = self.id
        self.fingerTable = OrderedDict()
        self.seed_url = seed_url

    def getSuccessorPetition(serverAddress, keyID):
        with grpc.insecure_channel(f'{serverAddress[0]}:{serverAddress[1]}') as channel:
            stub = node_service_pb2_grpc.NodeService(channel)
            request = node_service_pb2.NodeId(id=keyID)
            response = stub.LookUpID(request)
            return [response.identifier, (response.Address.ip, response.Address.port)]        

    def getConnectPeerPetition(serverAddress, address):
        with grpc.insecure_channel(f'{serverAddress[0]}:{serverAddress[1]}') as channel:
            stub = node_service_pb2_grpc.NodeService(channel)
            request = node_service_pb2.Address(ip=address[0], port=address[1])
            response = stub.ConnectPeer(request)
            return (response.Address.ip, response.Address.port)
        
    def UpdatePredSuccPetition(serverAddress, action, addressr):
        with grpc.insecure_channel(f'{serverAddress[0]}:{serverAddress[1]}') as channel:
            stub = node_service_pb2_grpc.NodeService(channel)
            address = node_service_pb2.Address(ip=addressr[0], port=addressr[1])
            request = node_service_pb2.UpdatePredSuccRequest(identifier=action, address=address)
            response = stub.UpdatePredSucc(request)
            return (response.Address.ip, response.Address.port)
        
    def UpdateFingerTablePetition(serverAddress):
        with grpc.insecure_channel(f'{serverAddress[0]}:{serverAddress[1]}') as channel:
            stub = node_service_pb2_grpc.NodeService(channel)
            request = node_service_pb2.DefaultServiceRequest()
            response = stub.UpdateFingerTable(request)
            return (response.Address.ip, response.Address.port)        

    def getSuccessor(self, address, keyID):
        rDataList = [1, address]
        recvIPPort = rDataList[1]
        while rDataList[0] == 1:
            try:               
                response = self.getSuccessorPetition(recvIPPort, keyID)           
                rDataList = response
                recvIPPort = rDataList[1]
            except grpc.RpcError as e:
                print(f"Request error while getting successor: {e}")
                break
        return recvIPPort

    def sendJoinRequest(self, ip, port):
        try:
            recvIPPort = self.getSuccessor((ip, port), self.id)
            response = self.getConnectPeerPetition(recvIPPort, self.address)
            rDataList = []           
            rDataList = response
            self.pred = rDataList[0]
            self.predID = getHash(self.pred[0] + ":" + str(self.pred[1]))
            self.succ = recvIPPort
            self.succID = getHash(recvIPPort[0] + ":" + str(recvIPPort[1]))
            response = self.UpdatePredSuccPetition(self.pred, 1, self.address)
            return "Nodo unido correctamente"
        except grpc.RpcError as e:
            print(f"Request error: {e}")
            return "Request error", 500
        except Exception as e:
            print(f"Unexpected error: {e}")
            return "Unexpected error", 500
        
    def lookupID(self, keyID):
        sDataList = []
        if self.id == keyID:
            sDataList = [0, self.address]
        elif self.succID == self.id:
            sDataList = [0, self.address]
        elif self.id > keyID:
            if self.predID < keyID:
                sDataList = [0, self.address]
            elif self.predID > self.id:
                sDataList = [0, self.address]
            else:
                sDataList = [1, self.pred]
        else:
            if self.id > self.succID:
                sDataList = [0, self.succ]
            else:
                value = ()
                for key, value in self.fingerTable.items():
                    if key >= keyID:
                        break
                value = self.succ
                sDataList = [1, value]
        return sDataList
    
    def updateFTable(self):
        for i in range(MAX_BITS):
            entryId = (self.id + (2 ** i)) % MAX_NODES
            if self.succ == self.address:
                self.fingerTable[entryId] = (self.id, self.address)
                continue
            recvIPPort = self.getSuccessor(self.succ, entryId)
            recvId = getHash(recvIPPort[0] + ":" + str(recvIPPort[1]))
            self.fingerTable[entryId] = (recvId, recvIPPort)

    def updateOtherFTables(self):
        here = self.succ
        while True:
            if here == self.address:
                break
            try:
                response = self.UpdateFingerTablePetition(here)            
                here = response
                if here == self.succ:
                    break
            except grpc.RpcError as e:
                print(f"Error en la conexión al actualizar otras tablas de finger: {e}")
    
    def joinNode(self, peerIPport):
        if peerIPport:
            peerID = getHash(peerIPport[0] + ":" + str(peerIPport[1]))
            oldPred = self.pred
            self.pred = peerIPport
            self.predID = peerID
            sDataList = [oldPred]
            time.sleep(0.1)
            self.updateFTable()
            self.updateOtherFTables()
            return sDataList
        
    def leaveNetwork(self):
        self.UpdatePredSuccPetition(self.succ, 0, self.pred)
        self.UpdatePredSuccPetition(self.pred, 1, self.succ)
        self.updateOtherFTables()
        self.pred = (self.ip, self.grpc_port)
        self.predID = self.id
        self.succ = (self.ip, self.grpc_port)
        self.succID = self.id
        self.fingerTable.clear()
        return self.address, "ha salido de la red"
    
    def printFTable(self):
        print("Printing F Table")
        for key, value in self.fingerTable.items():
            print("KeyID:", key, "Value", value)
    
    def start(self):
        grpc_port = self.port
        server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
        node_service_pb2_grpc.add_NodeServiceServicer_to_server(Node_service(self), server)
        file_service_pb2_grpc.add_FileServiceServicer_to_server(FileServicer(self), server)
        server.add_insecure_port(f"{self.ip}:{grpc_port}")
        server.start()
        print(f"gRPC Server started on {self.ip}:{grpc_port}")
        server.wait_for_termination()
        
    
