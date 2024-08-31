import os
from collections import OrderedDict
from concurrent import futures
import threading
import time
from urllib.parse import urlparse

import grpc
from node_manager.hash import getHash
from proto import file_service_pb2, file_service_pb2_grpc, node_service_pb2, node_service_pb2_grpc

myNode = None
end = False
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
                uri=f"http://{self.node.ip}:{self.node.port}/files/{os.path.basename(self.node.directory)}/{filename}"
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
        
    def LookUpID(self, request, context):
        response = self.node.lookupID(request.id)
        print(response[1])
        ip, port = response[1]
        address = node_service_pb2.Address(ip=ip, port=port)
        return node_service_pb2.JoinNodeResponse(identifier=response[0], address=address)

    
    def ConnectPeer(self, request, context):
        try:
            address = request
            print("Connection with:", address.ip, ":", address.port)
            print("Join network request received")
            ip, port = self.node.joinNode(address)
            return node_service_pb2.Address(ip=ip, port=port)
        except Exception as e:
            print(f"Error occurred: {e}")
            return node_service_pb2.Address(ip="0.0.0.0", port=0)
    
    def LeaveNetwork(self, request, context):
        return self.node.leaveNetwork()
    
    def GetFingerTable(self, request, context):
        return self.node.printFTable()
    
    def UpdatePredSucc(self, request, context):       
        if request.identifier == 1:
            self.node.updateSucc(request)
            ip, port = self.node.succ
            return node_service_pb2.Address(ip=ip, port=port)
        else:
            self.node.updatePred(request)
            ip, port = self.node.pred
            return node_service_pb2.Address(ip=ip, port=port)

    def UpdateFingerTable(self, request, context):
        self.node.updateFTable()
        ip, port = self.node.succ
        return node_service_pb2.Address(ip=ip, port=port)
    
    def GetPredSucc(self, request, context):
        return {"My ID": self.node.id, "Predecessor": self.node.predID, "Successor": self.node.succID}
        
    def SearchFile(self, request, context):
        try:
            search_term = request.filename
            files = self.node.searchFile(search_term)
            return node_service_pb2.SearchFileResponse(files=files)
        except Exception as e:
            print(f"Error occurred: {e}")
            return node_service_pb2.SearchFileResponse()
class Node:
    def __init__(self, ip, port, directory=None, seed_url=None):
        self.filenameList = []
        self.ip = ip
        self.port = port
        self.directory = self.get_directory_for_port(port)
        self.address = (ip, port)
        self.id = getHash(ip + ":" + str(port))
        self.pred = (ip, port)
        self.predID = self.id
        self.succ = (ip, port)
        self.succID = self.id
        self.fingerTable = OrderedDict()
        self.seed_url = seed_url
        # self.lock = threading.Lock()

    # def get_directory_for_port(self, port):
    #     if 2000 <= port <= 2999:
    #         return "files/nodos2000"
    #     elif 3000 <= port <= 3999:
    #         return "files/nodos3000"
    #     elif port >= 4000:
    #         return "files/nodos4000"
    #     else:
    #         return "files/default"  # Default directory for any other port range

    def get_directory_for_port(self, port):
        return "files"  # All nodes will use the same directory


    def getSuccessorPetition(self, serverAddress, keyID):
        with grpc.insecure_channel(f'{serverAddress[0]}:{serverAddress[1]}') as channel:
            stub = node_service_pb2_grpc.NodeServiceStub(channel)
            request = node_service_pb2.NodeId(id=keyID)
            response = stub.LookUpID(request)
            return [response.identifier, (response.address.ip, response.address.port)]       

    def getConnectPeerPetition(self, serverAddress, address):
        with grpc.insecure_channel(f'{serverAddress[0]}:{serverAddress[1]}') as channel:
            stub = node_service_pb2_grpc.NodeServiceStub(channel)
            request = node_service_pb2.Address(ip=address[0], port=address[1])
            response = stub.ConnectPeer(request)
            return (response.ip, response.port)
        
    def UpdatePredSuccPetition(self, serverAddress, action, addressr):
        with grpc.insecure_channel(f'{serverAddress[0]}:{serverAddress[1]}') as channel:
            stub = node_service_pb2_grpc.NodeServiceStub(channel)
            ip, port =  addressr
            address = node_service_pb2.Address(ip=ip, port=port)
            request = node_service_pb2.UpdatePredSuccRequest(identifier=action, address=address)
            response = stub.UpdatePredSucc(request)
            return (response.ip, response.port)
        
    def UpdateFingerTablePetition(self, serverAddress):
        with grpc.insecure_channel(f'{serverAddress[0]}:{serverAddress[1]}') as channel:
            stub = node_service_pb2_grpc.NodeServiceStub(channel)
            request = node_service_pb2.DefaultRequest()
            response = stub.UpdateFingerTable(request)
            return (response.ip, response.port)        

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
        # with self.lock:
            try:
                recvIPPort = self.getSuccessor((ip, port), self.id)
                response = self.getConnectPeerPetition(recvIPPort, self.address)
                self.pred = response
                self.predID = getHash(self.pred[0] + ":" + str(self.pred[1]))
                self.succ = recvIPPort
                self.succID = getHash(recvIPPort[0] + ":" + str(recvIPPort[1]))
                response = self.UpdatePredSuccPetition(self.pred, 1, self.address)
                print("Nodo unido correctamente")
            except grpc.RpcError as e:
                print(f"Request error: {e}")
                return "Request error", 500
            except Exception as e:
                print(f"Unexpected error: {e}")
                return "Unexpected error", 500
        
    def lookupID(self, keyID):
        # with self.lock:
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
        # with self.lock:
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
        # with self.lock:
            if peerIPport:
                peerID = getHash(peerIPport.ip + ":" + str(peerIPport.port))
                oldPred = self.pred
                self.pred = peerIPport
                self.predID = peerID
                sDataList = [oldPred]
                time.sleep(0.1)
                self.updateFTable()
                self.updateOtherFTables()
                return_value = sDataList[0]
                return return_value
           
        
    def leaveNetwork(self):
        # with self.lock:
            self.UpdatePredSuccPetition(self.succ, 0, self.pred)
            self.UpdatePredSuccPetition(self.pred, 1, self.succ)
            self.updateOtherFTables()
            self.pred = (self.ip, self.port)
            self.predID = self.id
            self.succ = (self.ip, self.port)
            self.succID = self.id
            self.fingerTable.clear()
            return self.address, "ha salido de la red"
    
    def updateSucc(self, rDataList):
        # with self.lock:
            newSucc = rDataList.address
            newSucc = (newSucc.ip, newSucc.port)
            self.succ = newSucc
            self.succID = getHash(newSucc[0] + ":" + str(newSucc[1]))

    def updatePred(self, rDataList):
        # with self.lock:
            newPred = rDataList.address
            newPred = (newPred.ip, newPred.port)
            self.pred = newPred
            self.predID = getHash(newPred[0] + ":" + str(newPred[1]))
    
    def printFTable(self):
        # with self.lock:
            print("Printing F Table")
            for key, value in self.fingerTable.items():
                print("KeyID:", key, "Value", value)
    

    def searchFile(self, search_term):
        files = []
        if self.directory:
            for filename in os.listdir(self.directory):
                if search_term.lower() in filename.lower():
                    file_info = node_service_pb2.FileInfo(
                        name=filename,
                        uri=f"http://{self.ip}:{self.port}/files/{os.path.basename(self.directory)}/{filename}"
                    )
                    files.append(file_info)
        return files

    def searchFileInNetwork(self, search_term):
        # with self.lock:
            current_node = self.address
            visited_nodes = set()

            while True:
                if current_node in visited_nodes:
                    break
                visited_nodes.add(current_node)

                try:
                    with grpc.insecure_channel(f'{current_node[0]}:{current_node[1]}') as channel:
                        stub = node_service_pb2_grpc.NodeServiceStub(channel)
                        request = node_service_pb2.SearchFileRequest(filename=search_term)
                        response = stub.SearchFile(request)

                        if response.files:
                            return response.files

                        next_node_request = node_service_pb2.NodeId(id=self.succID)
                        next_node_response = stub.LookUpID(next_node_request)
                        next_node = (next_node_response.address.ip, next_node_response.address.port)
                        
                        if next_node == self.address:
                            break  
                        
                        current_node = next_node

                except grpc.RpcError as e:
                    print(f"Error searching node {current_node}: {e}")
                    current_node = self.succ

            return []  


    def dummyUpload(self, filename, target_node):
        try:
            with grpc.insecure_channel(f'{target_node[0]}:{target_node[1]}') as channel:
                stub = file_service_pb2_grpc.FileServiceStub(channel)
                request = file_service_pb2.UploadRequest(filename=filename)
                response = stub.DummyUpload(request)
                print(f"Upload response: {response.message}")
        except grpc.RpcError as e:
            print(f"Error in dummy upload: {e}")

    def dummyDownload(self, filename):
        try:
            with grpc.insecure_channel(f'{self.ip}:{self.port}') as channel:
                stub = file_service_pb2_grpc.FileServiceStub(channel)
                request = file_service_pb2.DownloadRequest(filename=filename)
                response = stub.DummyDownload(request)
                print(f"Download response: {response.message}")
        except grpc.RpcError as e:
            print(f"Error in dummy download: {e}")

    def printMenu(self):
        print("\n1. Join Network\n2. Leave Network\n3. Upload File\n4. Download File")
        print("5. Print Finger Table\n6. Print my predecessor and successor\n7. Search File")
        print("8. List Files on Each Node\nf. Terminar proceso")

    def asAClientThread(self):
        self.printMenu()
        userChoice = input()
        if userChoice == "1":
            parsed_url = urlparse(self.seed_url)
            ip = parsed_url.hostname
            port = parsed_url.port
            self.sendJoinRequest(ip, int(port))
        elif userChoice == "2":
            self.leaveNetwork()
        elif userChoice == "3":
            filename = input("Enter filename to upload: ")
            fileID = getHash(filename)
            recvIPport = self.getSuccessor(self.succ, fileID)
            self.dummyUpload(filename, recvIPport)
        elif userChoice == "4":
            filename = input("Enter filename to download: ")
            self.dummyDownload(filename)
        elif userChoice == "5":
            self.printFTable()
        elif userChoice == "6":
            print("My ID:", self.id, "Predecessor:", self.predID, "Successor:", self.succID)
        elif userChoice == "7":  # Opción para buscar archivos
            search_term = input("Enter search term: ")
            files = self.searchFileInNetwork(search_term)
            if files:
                print("Files found:")
                for file in files:
                    print(f"Name: {file.name}, URI: {file.uri}")
            else:
                print("No files found.")
        elif userChoice == "8":
            self.listFiles()
        elif userChoice == "f":
            global end
            end = True

    def listFiles(self):
        try:
            with grpc.insecure_channel(f'{self.ip}:{self.port}') as channel:
                stub = file_service_pb2_grpc.FileServiceStub(channel)
                request = file_service_pb2.Empty()
                response = stub.ListFiles(request)
                
                print("Files in the current node:")
                for file in response.files:
                    print(f"Name: {file.name}, URI: {file.uri}")
        except grpc.RpcError as e:
            print(f"Error in listFiles: {e}")

    def start(self):
        grpc_port = self.port
        server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
        node_service_pb2_grpc.add_NodeServiceServicer_to_server(Node_service(self), server)
        file_service_pb2_grpc.add_FileServiceServicer_to_server(FileServicer(self), server)
        server.add_insecure_port(f"{self.ip}:{grpc_port}")
        server.start()
        print(f"gRPC Server started on {self.ip}:{grpc_port}")
        while end != True:
            print("Listening to other clients")   
            self.asAClientThread()
        
        server.wait_for_termination()
        
    
