from flask import Flask, send_from_directory, jsonify
import json
import os

app = Flask(__name__)

# Cargar configuración
with open('upload_download_service/config.json') as config_file:
    config = json.load(config_file)

@app.route('/files/download/<filename>', methods=['GET'])
def download_file(filename):
    try:
        directory = config['download_directory']
        # Asegúrate de que la ruta completa sea correcta
        full_path = os.path.join(os.getcwd(), directory)
        print(f"Attempting to send file from: {full_path}")  # Debugging
        return send_from_directory(full_path, filename)
    except Exception as e:
        print(f"Error: {e}")  # Debugging
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host=config['ip'], port=config['port'])
