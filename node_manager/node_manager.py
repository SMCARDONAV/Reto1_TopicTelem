import yaml
from flask import Flask, jsonify, request
from .node import Node
from node_manager.hash import getHash

# Configuración por defecto para IP y puertos
IP = "127.0.0.1"
FLASK_PORT = 2000
GRPC_PORT = 2001  # Puerto separado para gRPC

myNode = None  # Inicializa como None

app = Flask(__name__)

def create_node(ip, grpc_port, directory=None, seed_url=None):
    global myNode
    myNode = Node(ip, grpc_port, directory, seed_url)
    return myNode

@app.route('/')
def home():
    return "Node Manager Home"

@app.route("/api/joinNetwork", methods=['POST'])
def join_network():
    try:
        # Obtener los datos en formato de lista
        received_data = request.get_json()
        
        # Verificar el formato de los datos recibidos
        if not isinstance(received_data, list) or len(received_data) != 2:
            return jsonify({"error": "Invalid data format. Expected a list with IP and port."}), 400

        ip = received_data[0]
        port = received_data[1]
        
        # Validar IP y puerto
        if not isinstance(ip, str) or not isinstance(port, int):
            return jsonify({"error": "Invalid data format. IP should be a string and port should be an integer."}), 400

        print('joinNetwork')
        message = myNode.sendJoinRequest(ip, int(port))
        return jsonify(message)
    
    except Exception as e:
        # Log del error
        print(f"Error occurred: {e}")
        return jsonify({"error": "An unexpected error occurred."}), 500
    
@app.route("/api/leaveNetwork", methods=['POST'])
def leave_network():
    return jsonify(myNode.leaveNetwork())

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
    return jsonify(myNode.printFTable())

@app.route("/api/predsucc", methods=['GET'])
def get_pred_succ():
    return jsonify({"My ID": myNode.id, "Predecessor": myNode.predID, "Successor": myNode.succID})

@app.route("/api/lookUpId/<int:keyID>", methods=['GET'])
def joinNode(keyID):
    return jsonify(myNode.lookupID(keyID))

@app.route("/api/connectpeer", methods=['POST'])
def connectPeer():
    received_data = request.get_json()
    address = received_data[0]
    print("Connection with:", address[0], ":", address[1])
    print("Join network request received")
    return jsonify(myNode.joinNode(address))

@app.route("/api/updateFingerTable", methods=['POST'])
def updateFingerTable():
    myNode.updateFTable()
    return jsonify(myNode.succ)

@app.route("/api/updatePredSucc", methods=['POST'])
def updatePredSucc():
    received_data = request.get_json()
    if received_data[0] == 1:
        myNode.updateSucc(received_data)
        return jsonify(myNode.succ)
    else:
        myNode.updatePred(received_data)
        return jsonify(myNode.pred)

@app.route("/api/fileClient", methods=['POST'])
def transferFile():
    # print("Connection with:", address[0], ":", address[1])
    print("Upload/Download request received")
    # myNode.transferFile(connection, address, rDataList)

if __name__ == "__main__":
    import sys
    import os
    from threading import Thread
    from node_manager import node_app

    # Crea y ejecuta el nodo
    def create_and_run_node(ip, grpc_port):
        node = create_node(ip, grpc_port)
        return node

    def start_grpc_server(node):
        grpc_thread = Thread(target=node.start)
        grpc_thread.start()
        print(f"gRPC server started on {ip}:{grpc_port}")

    def start_flask_app(ip, port):
        app.run(host='0.0.0.0', port=port, debug=True)

    # Configura el puerto de gRPC y el puerto de Flask
    ip = IP
    grpc_port = GRPC_PORT
    flask_port = FLASK_PORT

    # Crea y ejecuta el nodo
    node = create_and_run_node(ip, grpc_port)

    # Inicia el servidor gRPC
    start_grpc_server(node)

    # Inicia la aplicación Flask
    start_flask_app(ip, flask_port)
