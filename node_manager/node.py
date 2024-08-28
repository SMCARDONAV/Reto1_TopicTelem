# from collections import OrderedDict
# import time
# import requests
# import os
# import grpc
# from concurrent import futures
# from proto import file_service_pb2
# from proto import file_service_pb2_grpc

# from node_manager.hash import getHash

# MAX_BITS = 10
# MAX_NODES = 2 ** MAX_BITS
# api_connect_peer = "/api/connectpeer"
# api_update_pred_succ = "/api/updatePredSucc"
# api_lookUpId = "/api/lookUpId/"
# api_update_finger_table = "/api/updateFingerTable"

# class FileServicer(file_service_pb2_grpc.FileServiceServicer):
#     def __init__(self, node):
#         self.node = node

#     def ListFiles(self, request, context):
#         files = [
#             file_service_pb2.FileInfo(
#                 name=filename,
#                 uri=f"http://{self.node.ip}:{self.node.port}/files/{filename}"
#             )
#             for filename in os.listdir(self.node.directory)
#             if os.path.isfile(os.path.join(self.node.directory, filename))
#         ]
#         return file_service_pb2.ListFilesResponse(files=files)
    
#     def DummyDownload(self, request, context):
#         return file_service_pb2.DownloadResponse(message=f"Dummy download of {request.filename}")

#     def DummyUpload(self, request, context):
#         return file_service_pb2.UploadResponse(message=f"Dummy upload of {request.filename}")

# class Node:
#     def __init__(self, ip, port, directory=None, seed_url=None):
#         self.filenameList = []
#         self.ip = ip
#         self.port = port
#         self.directory = directory
#         self.address = (ip, port)
#         self.id = getHash(ip + ":" + str(port))
#         self.pred = (ip, port)
#         self.predID = self.id
#         self.succ = (ip, port)
#         self.succID = self.id
#         self.fingerTable = OrderedDict()
#         self.seed_url = seed_url

#     def getSuccessor(self, address, keyID):
#         rDataList = [1, address]  # Default values to run while loop
#         recvIPPort = rDataList[1]
#         while rDataList[0] == 1:
#             try:
#                 url = self.urlFormatter(recvIPPort, api_lookUpId, str(keyID))
#                 response = requests.get(url)
#                 response.raise_for_status()  # Raise an error for bad status codes
#                 if response.status_code == 200:
#                     rDataList = response.json()
#                     recvIPPort = rDataList[1]
#             except requests.exceptions.RequestException as e:
#                 print(f"Request error while getting successor: {e}")
#                 break
#         return recvIPPort

#     def urlFormatter(self, address, api, urlParam=None):
#         ip, port = address
#         if urlParam is not None:
#             return f"http://{ip}:{port}{api}{urlParam}"
#         else:
#             return f"http://{ip}:{port}{api}"

#     def sendJoinRequest(self, ip, port):
#         try:
#             recvIPPort = self.getSuccessor((ip, port), self.id)
#             url = self.urlFormatter(recvIPPort, api_connect_peer)
#             request = [self.address]
#             response = requests.post(url, json=request)
#             rDataList = []
#             if response.status_code == 200:
#                 rDataList = response.json()
#                 self.pred = rDataList[0]
#                 self.predID = getHash(self.pred[0] + ":" + str(self.pred[1]))
#                 self.succ = recvIPPort
#                 self.succID = getHash(recvIPPort[0] + ":" + str(recvIPPort[1]))
#                 url = self.urlFormatter(self.pred, api_update_pred_succ)
#                 request = [1, self.address]
#                 requests.post(url, json=request)
#                 return "Nodo unido correctamente"
#             else:
#                 return "Failed to join network: response error", response.status_code
#         except requests.exceptions.RequestException as e:
#             print(f"Request error: {e}")
#             return "Request error", 500
#         except Exception as e:
#             print(f"Unexpected error: {e}")
#             return "Unexpected error", 500

#     def updateFTable(self):
#         for i in range(MAX_BITS):
#             entryId = (self.id + (2 ** i)) % MAX_NODES
#             if self.succ == self.address:
#                 self.fingerTable[entryId] = (self.id, self.address)
#                 continue
#             recvIPPort = self.getSuccessor(self.succ, entryId)
#             recvId = getHash(recvIPPort[0] + ":" + str(recvIPPort[1]))
#             self.fingerTable[entryId] = (recvId, recvIPPort)

#     def updateOtherFTables(self):
#         here = self.succ
#         while True:
#             if here == self.address:
#                 break
#             try:
#                 url = self.urlFormatter(here, api_update_finger_table)
#                 response = requests.post(url)
#                 here = response.json()
#                 if here == self.succ:
#                     break
#             except requests.exceptions.RequestException as e:
#                 print(f"Error en la conexión al actualizar otras tablas de finger: {e}")

#     def sendFile(self, connection, filename):
#         print("Sending file:", filename)

#     def leaveNetwork(self):
#         url = self.urlFormatter(self.succ, api_update_pred_succ)
#         request = [0, self.pred]
#         requests.post(url, json=request)
#         urlPred = self.urlFormatter(self.pred, api_update_pred_succ)
#         requestPred = [1, self.succ]
#         requests.post(urlPred, json=requestPred)
#         self.updateOtherFTables()
#         self.pred = (self.ip, self.grpc_port)
#         self.predID = self.id
#         self.succ = (self.ip, self.grpc_port)
#         self.succID = self.id
#         self.fingerTable.clear()
#         return self.address, "ha salido de la red"

#     def uploadFile(self, filename, recvIPport, replicate):
#         print("Uploading file", filename)

#     def downloadFile(self, filename):
#         print("Downloading file", filename)
#         fileID = getHash(filename)
#         recvIPport = self.getSuccessor(self.succ, fileID)
#         urlFiles = self.urlFormatter(recvIPport, "/api/fileClient")
#         requestFileClient = [0, filename]
#         requests.post(urlFiles, json=requestFileClient)

#     def printFTable(self):
#         print("Printing F Table")
#         for key, value in self.fingerTable.items():
#             print("KeyID:", key, "Value", value)

#     def receiveFile(self, connection, filename):
#         pass

#     def printMenu(self):
#         print("\n1. Join Network\n2. Leave Network\n3. Upload File\n4. Download File")
#         print("5. Print Finger Table\n6. Print my predecessor and successor")

#     def lookupID(self, keyID):
#         sDataList = []
#         if self.id == keyID:
#             sDataList = [0, self.address]
#         elif self.succID == self.id:
#             sDataList = [0, self.address]
#         elif self.id > keyID:
#             if self.predID < keyID:
#                 sDataList = [0, self.address]
#             elif self.predID > self.id:
#                 sDataList = [0, self.address]
#             else:
#                 sDataList = [1, self.pred]
#         else:
#             if self.id > self.succID:
#                 sDataList = [0, self.succ]
#             else:
#                 value = ()
#                 for key, value in self.fingerTable.items():
#                     if key >= keyID:
#                         break
#                 value = self.succ
#                 sDataList = [1, value]
#         return sDataList

#     def joinNode(self, peerIPport):
#         if peerIPport:
#             peerID = getHash(peerIPport[0] + ":" + str(peerIPport[1]))
#             oldPred = self.pred
#             self.pred = peerIPport
#             self.predID = peerID
#             sDataList = [oldPred]
#             time.sleep(0.1)
#             self.updateFTable()
#             self.updateOtherFTables()
#             return sDataList

#     def updateSucc(self, rDataList):
#         newSucc = rDataList[1]
#         self.succ = newSucc
#         self.succID = getHash(newSucc[0] + ":" + str(newSucc[1]))

#     def updatePred(self, rDataList):
#         newPred = rDataList[1]
#         self.pred = newPred
#         self.predID = getHash(newPred[0] + ":" + str(newPred[1]))

#     def transferFile(self, connection, address, rDataList):
#         print("Transferring file")

#     def asAClientThread(self):
#         self.printMenu()
#         userChoice = input()
#         if userChoice == "1":
#             ip = input("Enter IP to connect: ")
#             port = input("Enter port: ")
#             self.sendJoinRequest(ip, int(port))
#         elif userChoice == "2":
#             self.leaveNetwork()
#         elif userChoice == "3":
#             filename = input("Enter filename to upload: ")
#             replicate = input("Enter replicate (yes/no): ").lower() == "yes"
#             self.uploadFile(filename, self.succ, replicate)
#         elif userChoice == "4":
#             filename = input("Enter filename to download: ")
#             self.downloadFile(filename)
#         elif userChoice == "5":
#             self.printFTable()
#         elif userChoice == "6":
#             print("Predecessor:", self.pred)
#             print("Successor:", self.succ)
#         else:
#             print("Invalid choice")

#     def start(self):
#         grpc_port = self.port  # Asegúrate de que self.port esté definido
#         server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
#         file_service_pb2_grpc.add_FileServiceServicer_to_server(FileServicer(self), server)
#         server.add_insecure_port(f"{self.ip}:{grpc_port}")
#         server.start()
#         print(f"gRPC Server started on {self.ip}:{grpc_port}")
#         server.wait_for_termination()
