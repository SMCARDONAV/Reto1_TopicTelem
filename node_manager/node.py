from collections import OrderedDict
import time
import requests
import re

from node_manager.hash import getHash

MAX_BITS = 10
MAX_NODES = 2 ** MAX_BITS
api_connect_peer = "/api/connectpeer/"
api_update_pred_succ = "/api/updatePredSucc"
api_lookUpId = "/api/lookUpId/"
api_update_finger_table = "/api/updateFingerTable"


class Node:
    def __init__(self, ip, port):
        self.filenameList = []
        self.ip = ip
        self.port = port
        self.address = (ip, port)
        self.id = getHash(ip + ":" + str(port))
        self.pred = (ip, port)
        self.predID = self.id
        self.succ = (ip, port)
        self.succID = self.id
        self.fingerTable = OrderedDict()

    def getSuccessor(self, address, keyID):
        rDataList = [1, address]      # Deafult values to run while loop
        recvIPPort = rDataList[1]
        # TODO: Pasar url a otro lugar
        # ipPort = str(address[0]) + str(address[1])
        # url = "http://"+ipPort+"/api/lookUpId/"+str(keyID)
        while rDataList[0] == 1:
            # peerSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                url = self.urlFormatter(recvIPPort, api_lookUpId, str(keyID))
                # peerSocket.connect(recvIPPort)
                response = requests.get(url)
                # Send continous lookup requests until required peer ID
                # sDataList = [3, keyID]
                #   peerSocket.sendall(pickle.dumps(sDataList))
                # Do continous lookup until you get your postion (0)
                if response.status_code == 200:
                    rDataList = response.json()
                    recvIPPort = rDataList[1]
                # peerSocket.close()
            except requests.exceptions.HTTPError:
                print("Connection denied while getting Successor")
        # print(rDataList)
        return recvIPPort

    def urlFormatter(self, address, api, urlParam=None):
        print(address)
        # match = re.match(r'^(\d{1,3}(?:\.\d{1,3}){3})(\d{1,5})$', address)
        # print(match)
        # if match:
        #     ip = match.group(1)  # Captura la IP
        #     port = match.group(2)  # Captura el puerto            
        # else:
            # raise ValueError("Formato no válido")
        
        ip, port = address
        if urlParam is not None:
            return "http://"+ip+":"+str(port)+api+urlParam
        else:
            return "http://"+ip+":"+str(port)+api

    def sendJoinRequest(self, ip, port):
        try:
            recvIPPort = self.getSuccessor((ip, port), self.id)
            # TODO: Pasar url a otro lugar
            print(recvIPPort)
            url = self.urlFormatter(recvIPPort, api_connect_peer, str(self.address))
            # url = "http://"+recvIPPort+"/api/connectpeer/"+self.address
            response = requests.get(url)
            # peerSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            # peerSocket.connect(recvIPPort)
            # sDataList = [0, self.address]
            # peerSocket.sendall(pickle.dumps(sDataList))
            # rDataList = pickle.loads(peerSocket.recv(buffer))
            # Updating pred and succ
            # print('before', self.predID, self.succID)
            rDataList = []
            if response.status_code == 200:
                rDataList = response.json()
                self.pred = rDataList[0]
                self.predID = getHash(self.pred[0] + ":" + str(self.pred[1]))
                self.succ = recvIPPort
                self.succID = getHash(recvIPPort[0] + ":" + str(recvIPPort[1]))
            # print('after', self.predID, self.succID)
            # Tell pred to update its successor which is now me
                # sDataList = [4, 1, self.address]
                # url = "http://"+self.pred+"/api/updatePredSucc"
                url = self.urlFormatter(self.pred, api_update_pred_succ)
                request = [1, self.address]
                # pSocket2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                # pSocket2.connect(self.pred)
                # pSocket2.sendall(pickle.dumps(sDataList))
                requests.post(url, json=request)
                # pSocket2.close()
                # peerSocket.close()
                return "Nodo unido correctamente"
        except requests.exceptions.HTTPError:
            print("Connection error")

    def updateFTable(self):
        for i in range(MAX_BITS):
            entryId = (self.id + (2 ** i)) % MAX_NODES
            # If only one node in network
            if self.succ == self.address:
                self.fingerTable[entryId] = (self.id, self.address)
                continue
            # If multiple nodes in network, we find succ for each entryID
            recvIPPort = self.getSuccessor(self.succ, entryId)
            recvId = getHash(recvIPPort[0] + ":" + str(recvIPPort[1]))
            self.fingerTable[entryId] = (recvId, recvIPPort)
        # self.printFTable()

    def updateOtherFTables(self):
        here = self.succ
        while True:
            if here == self.address:
                break
            # pSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                # pSocket.connect(here)  # Connecting to server
                # url = "http://"+here+"/api/updateFingerTable"
                url = self.urlFormatter(here, api_update_finger_table)
                # pSocket.sendall(pickle.dumps([5]))
                response = requests.post(url)
                here = response.json()
                # pSocket.close()
                if here == self.succ:
                    break
            except requests.exceptions.HTTPError:
                print("Connection error")

    def sendFile(self, connection, filename):
        print("Sending file:", filename)
        # try:
        #     # Reading file data size
        #     with open(filename, 'rb') as file:
        #         data = file.read()
        #         print("File size:", len(data))
        #         fileSize = len(data)
        # except:
        #     print("File not found")
        # try:
        #     with open(filename, 'rb') as file:
        #         #connection.send(pickle.dumps(fileSize))
        #         while True:
        #             fileData = file.read(buffer)
        #             time.sleep(0.001)
        #             #print(fileData)
        #             if not fileData:
        #                 break
        #             connection.sendall(fileData)
        # except:
        #     pass#print("File not found in directory")
        # print("File sent")

    def leaveNetwork(self):
        # First inform my succ to update its pred
        # pSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # pSocket.connect(self.succ)
        url = "http://"+self.succ+"/api/updatePredSucc"
        request = [0, self.pred]
        # pSocket.sendall(pickle.dumps([4, 0, self.pred]))
        requests.post(url, json=request)
        # pSocket.close()
        # Then inform my pred to update its succ
        # pSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # pSocket.connect(self.pred)
        urlPred = "http://"+self.pred+"/api/updatePredSucc"
        # pSocket.sendall(pickle.dumps([4, 1, self.succ]))
        requestPred = [1, self.succ]
        # pSocket.close()
        requests.post(urlPred, json=requestPred)
        print("I had files:", self.filenameList)
        # And also replicating its files to succ as a client
        print("Replicating files to other nodes before leaving")
        for filename in self.filenameList:
            # pSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            # pSocket.connect(self.succ)
            urlFiles = "http://"+self.succ+"/api/fileClient"
            # sDataList = [1, 1, filename]
            requestFileClient = [1, filename]
            requests.post(urlFiles, json=requestFileClient)
            # pSocket.sendall(pickle.dumps(sDataList))
            # TODO: organizar envio de archivo
            # with open(filename, 'rb') as file:
            #     # Getting back confirmation
            #     #pSocket.recv(buffer)
            #     self.sendFile(pSocket, filename)
            #     #pSocket.close()
            #     print("File replicated")
            # pSocket.close()
        self.updateOtherFTables()   # Telling others to update their f tables
        self.pred = (self.ip, self.port)    # Chaning the pointers to default
        self.predID = self.id
        self.succ = (self.ip, self.port)
        self.succID = self.id
        self.fingerTable.clear()
        print(self.address, "has left the network")

    def uploadFile(self, filename, recvIPport, replicate):
        print("Uploading file", filename)
        # TODO: organizar logica para cargar archivos
        # # If not found send lookup request to get peer to upload file
        # sDataList = [1]
        # if replicate:
        #     sDataList.append(1)
        # else:
        #     sDataList.append(-1)
        # try:
        #     # Before doing anything check if you have the file or not
        #     file = open(filename, 'rb')
        #     file.close()
        #     sDataList = sDataList + [filename]
        #     cSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        #     cSocket.connect(recvIPport)
        #     cSocket.sendall(pickle.dumps(sDataList))
        #     self.sendFile(cSocket, filename)
        #     cSocket.close()
        #     print("File uploaded")
        # except IOError:
        #     print("File not in directory")
        # except socket.error:
        #     print("Error in uploading file")

    def downloadFile(self, filename):
        print("Downloading file", filename)
        fileID = getHash(filename)
        # First finding node with the file
        recvIPport = self.getSuccessor(self.succ, fileID)
        # sDataList = [1, 0, filename]
        # cSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # cSocket.connect(recvIPport)
        # cSocket.sendall(pickle.dumps(sDataList))
        urlFiles = "http://"+recvIPport+"/api/fileClient"
        requestFileClient = [0, filename]
        requests.post(urlFiles, json=requestFileClient)
        # Receiving confirmation if file found or not
        # TODO: terminar logica para descargar archivos
        # fileData = cSocket.recv(buffer)
        # if fileData == b"NotFound":
        #     print("File not found:", filename)
        # else:
        #     print("Receiving file:", filename)
        #     self.receiveFile(cSocket, filename)

    def printFTable(self):
        print("Printing F Table")
        for key, value in self.fingerTable.items():
            print("KeyID:", key, "Value", value)

    def receiveFile(self, connection, filename):
        # Receiving file in parts
        # If file already in directory
        fileAlready = False
        try:
            with open(filename, 'rb') as file:
                data = file.read()
                size = len(data)
                if size == 0:
                    print("Retransmission request sent")
                    fileAlready = False
                else:
                    print("File already present")
                    fileAlready = True
                return
        except FileNotFoundError:
            pass
        # receiving file size
        # fileSize = pickle.loads(connection.recv(buffer))
        # print("File Size", fileSize)
        if not fileAlready:
            pass
        # totalData = b''
        # recvSize = 0
        # try:
        #     with open(filename, 'wb') as file:
        #         while True:
        #             fileData = connection.recv(buffer)
        #             #print(fileData)
        #             recvSize += len(fileData)
        #             #print(recvSize)
        #             if not fileData:
        #                 break
        #             totalData += fileData
        #         file.write(totalData)
        # except ConnectionResetError:
        #     print("Data transfer interupted\nWaiting for system to stabilze")
        #     print("Trying again in 10 seconds")
        #     time.sleep(5)
        #     os.remove(filename)
        #     time.sleep(5)
        #     self.downloadFile(filename)
        #         # connection.send(pickle.dumps(True))

    def printMenu(self):
        print("\n1. Join Network\n2. Leave Network\n3. Upload File\n4. Download File")
        print("5. Print Finger Table\n6. Print my predecessor and successor")

    # SERVER
    def lookupID(self, keyID):
        # keyID = rDataList[1]
        sDataList = []
        # print(self.id, keyID)
        if self.id == keyID:        # Case 0: If keyId at self
            sDataList = [0, self.address]
        elif self.succID == self.id:  # Case 1: If only one node
            sDataList = [0, self.address]
        elif self.id > keyID:       # Case 2: Node id greater than keyId, ask pred
            if self.predID < keyID:   # If pred is higher than key, then self is the node
                sDataList = [0, self.address]
            elif self.predID > self.id:
                sDataList = [0, self.address]
            else:       # Else send the pred back
                sDataList = [1, self.pred]
        else:           # Case 3: node id less than keyId USE fingertable to search
            # IF last node before chord circle completes
            if self.id > self.succID:
                sDataList = [0, self.succ]
            else:
                value = ()
                for key, value in self.fingerTable.items():
                    if key >= keyID:
                        break
                value = self.succ
                sDataList = [1, value]
        # connection.sendall(pickle.dumps(sDataList))
        return sDataList
        # print(sDataList)

    def joinNode(self, peerIPport):
        if peerIPport:
            # peerIPport = rDataList[1]
            peerID = getHash(peerIPport[0] + ":" + str(peerIPport[1]))
            oldPred = self.pred
            # Updating pred
            self.pred = peerIPport
            self.predID = peerID
            # Sending new peer's pred back to it
            sDataList = [oldPred]
            # connection.sendall(pickle.dumps(sDataList))
            # Updating F table
            time.sleep(0.1)
            self.updateFTable()
            # Then asking other peers to update their f table as well
            self.updateOtherFTables()
            return sDataList
    
    def updateSucc(self, rDataList):
        newSucc = rDataList[2]
        self.succ = newSucc
        self.succID = getHash(newSucc[0] + ":" + str(newSucc[1]))
        # print("Updated succ to", self.succID)

    def updatePred(self, rDataList):
        newPred = rDataList[2]
        self.pred = newPred
        self.predID = getHash(newPred[0] + ":" + str(newPred[1]))
        # print("Updated pred to", self.predID)

    # TODO: ORGANIZAR LOGICA PARA TRANSFERIR ARCHIVOS
    def transferFile(self, connection, address, rDataList):
        print("transfer file")
        # # Choice: 0 = download, 1 = upload
        # choice = rDataList[1]
        # filename = rDataList[2]
        # fileID = getHash(filename)
        # # IF client wants to download file
        # if choice == 0:
        #     print("Download request for file:", filename)
        #     try:
        #         # First it searches its own directory (fileIDList). If not found, send does not exist
        #         if filename not in self.filenameList:
        #             connection.send("NotFound".encode('utf-8'))
        #             print("File not found")
        #         else:   # If file exists in its directory   # Sending DATA LIST Structure (sDataList):
        #             connection.send("Found".encode('utf-8'))
        #             self.sendFile(connection, filename)
        #     except ConnectionResetError as error:
        #         print(error, "\nClient disconnected\n\n")
        # # ELSE IF client wants to upload something to network
        # elif choice == 1 or choice == -1:
        #     print("Receiving file:", filename)
        #     fileID = getHash(filename)
        #     print("Uploading file ID:", fileID)
        #     self.filenameList.append(filename)
        #     self.receiveFile(connection, filename)
        #     print("Upload complete")
        #     # Replicating file to successor as well
        #     if choice == 1:
        #         if self.address != self.succ:
        #             self.uploadFile(filename, self.succ, False)

    # START

    def asAClientThread(self):
        # Printing options
        self.printMenu()
        userChoice = input()
        if userChoice == "1":
            ip = input("Enter IP to connect: ")
            port = input("Enter port: ")
            self.sendJoinRequest(ip, int(port))
        elif userChoice == "2":
            self.leaveNetwork()
        elif userChoice == "3":
            filename = input("Enter filename: ")
            fileID = getHash(filename)
            recvIPport = self.getSuccessor(self.succ, fileID)
            # TODO: organizar logica para cargar archivo
            self.uploadFile(filename, recvIPport, True)
        elif userChoice == "4":
            filename = input("Enter filename: ")
            # TODO: organizar logica para descargar archivos
            self.downloadFile(filename)
        elif userChoice == "5":
            self.printFTable()
        elif userChoice == "6":
            print("My ID:", self.id, "Predecessor:", self.predID, "Successor:", self.succID)
        # Reprinting Menu
        # self.printMenu()

    def start(self):
        # Accepting connections from other threads
        # threading.Thread(target=self.listenThread, args=()).start()
        # threading.Thread(target=self.pingSucc, args=()).start()
        # In case of connecting to other clients
        while True:
            print("Listening to other clients")   
            self.asAClientThread()
