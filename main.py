import sys
import os
from threading import Thread
import yaml

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from node_manager import node_app, node_manager

def load_config():
    with open('config.yaml', 'r') as f:
        return yaml.safe_load(f)

def create_and_run_node(ip, port):
    config = load_config()
    config['ip'] = ip
    config['port'] = port

    node = node_manager.create_node(
        config['ip'], 
        config['port'], 
        config.get('directory', None), 
        config.get('seed_url', None)
    )
    return node

def start_grpc_server(node):
    grpc_thread = Thread(target=node.start)
    grpc_thread.start()

def start_flask_app(ip, port):
    node_app.run(host='0.0.0.0', port=port)

def parse_arguments():
    if len(sys.argv) < 3:
        print("Arguments not supplied (Defaults used)")
        return "127.0.0.1", 2000
    return sys.argv[1], int(sys.argv[2])

def main():
    ip, flask_port = parse_arguments()
    grpc_port = flask_port + 1  # Por ejemplo, si Flask está en 2000, gRPC estará en 2001
    node = create_and_run_node(ip, grpc_port)
    start_grpc_server(node)
    start_flask_app(ip, flask_port)

if __name__ == "__main__":
    main()
