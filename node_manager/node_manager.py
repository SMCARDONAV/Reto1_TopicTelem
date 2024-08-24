from flask import Flask, jsonify, request
from node_manager.node import Node
from node_manager.hash import getHash

IP = "127.0.0.1"
PORT = 2000
myNode = Node(IP, PORT)

def create_node(IP, PORT):
    myNode = Node(IP, PORT)
    print("My ID is:", myNode.id)
    # myNode.start()

app = Flask(__name__)

@app.route("/api/joinNetwork", methods=['POST'])
def join_network():
    ip = input("Enter IP to connect: ")
    port = input("Enter port: ")
    message = myNode.sendJoinRequest(ip, int(port))
    return jsonify(message)

@app.route("/api/leaveNetwork", methods=['POST'])
def leave_network():
    myNode.leaveNetwork()

@app.route("/api/uploadFile", methods=['POST'])
def upload_file():
    filename = input("Enter filename: ")
    fileID = getHash(filename)
    recvIPport = myNode.getSuccessor(myNode.succ, fileID)
    # TODO: organizar logica para cargar archivo
    myNode.uploadFile(filename, recvIPport, True)

@app.route("/api/downloadFile", methods=['POST'])
def download_file():
    filename = input("Enter filename: ")
    # TODO: organizar logica para descargar archivos
    myNode.downloadFile(filename)

@app.route("/api/fingerTable", methods=['GET'])
def get_finger_table():
    myNode.printFTable()

@app.route("/api/predsucc", methods=['GET'])
def get_pred_succ():
    return jsonify("My ID:", myNode.id, "Predecessor:", myNode.predID, "Successor:", myNode.succID)

@app.route("/api/lookUpId/<int:keyID>", methods=['GET'])
def joinNode(keyID):
    return jsonify(myNode.lookupID(keyID))


@app.route("/api/connectpeer/<address>", methods=['GET'])
def connectPeer(address):
    print("Connection with:", address[0], ":", address[1])
    print("Join network request recevied")
    return jsonify(myNode.joinNode(address))


@app.route("/api/updateFingerTable", methods=['POST'])
def updateFingerTable():
    myNode.updateFTable()
    return jsonify(myNode.succ)


@app.route("/api/updatePredSucc", methods=['POST'])
def updatePredSucc():
    received_data = request.get_json()
    if received_data[1] == 1:
        myNode.updateSucc(received_data)
    else:
        myNode.updatePred(received_data)


@app.route("/api/fileClient", methods=['POST'])
def transferFile():
    # print("Connection with:", address[0], ":", address[1])
    print("Upload/Download request recevied")
    # myNode.transferFile(connection, address, rDataList)


# if __name__ == '__main__':
#     app.run(host='0.0.0.0', port=myNode.port)
