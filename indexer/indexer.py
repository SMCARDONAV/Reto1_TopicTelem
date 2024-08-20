from flask import Flask, jsonify
import os
import json

app = Flask(__name__)

# Cargar configuración
with open('indexer/config.json') as config_file:
    config = json.load(config_file)

@app.route('/files', methods=['GET'])
def list_files():
    try:
        files = os.listdir(config['directory'])
        return jsonify(files)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host=config['ip'], port=config['port'])
