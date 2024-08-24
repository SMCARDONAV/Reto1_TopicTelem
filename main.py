import sys
from threading import Thread
from node_manager import node_app
from node_manager.node_manager import create_node

IP = "127.0.0.1"
PORT = 2000

# def run_indexer():
#     indexer_app.run(host='0.0.0.0', port=5001)

# def run_upload_service():
#     upload_service_app.run(host='0.0.0.0', port=5002)

# def run_download_service():
#     download_service_app.run(host='0.0.0.0', port=5003)

def run_node():
    create_node(IP, PORT)
    node_app.run(host='0.0.0.0', port=PORT)

if len(sys.argv) < 3:
    print("Arguments not supplied (Defaults used)")
else:
    IP = sys.argv[1]
    PORT = int(sys.argv[2])

if __name__ == "__main__":
    # Thread(target=run_node).start()
    run_node()
# myNode = Node(IP, PORT)
# print("My ID is:", myNode.id)
# myNode.start()


#     Thread(target=run_indexer).start()
#     Thread(target=run_upload_service).start()
#     Thread(target=run_download_service).start()
