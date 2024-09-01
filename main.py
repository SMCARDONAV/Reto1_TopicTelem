import sys
import os
from threading import Thread
import yaml
from node_manager import node_service

sys.path.append(os.path.dirname(os.path.abspath(__file__)))


def load_config():
    with open('config.yaml', 'r') as f:
        return yaml.safe_load(f)
    

def create_and_run_node(ip, port):
    config = load_config()
    # config['ip'] = ip
    # config['port'] = port

    node = node_service.create_node(
        config['ip'], 
        config['port'], 
        config.get('directory', None), 
        config.get('seed_url', None)
    )
    return node


def start_grpc_server(node):
    # grpc_thread = Thread(target=node.start)
    # grpc_thread.start()
    # return grpc_thread
    node.start()


def parse_arguments():
    if len(sys.argv) < 3:
        print("Arguments not supplied (Defaults used)")
        return "127.0.0.1", 2000
    return sys.argv[1], int(sys.argv[2])


def main():
    ip, port = parse_arguments()
    node = create_and_run_node(ip, port)
    grpc_thread = start_grpc_server(node)
    grpc_thread.join()


if __name__ == "__main__":
    main()
