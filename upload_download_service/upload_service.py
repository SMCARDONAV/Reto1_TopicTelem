from flask import Flask, request, jsonify
import os
import json

app = Flask(__name__)

with open('upload_download_service/config.json') as config_file:
    config = json.load(config_file)

@app.route('/files/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    
    # Obtén la ruta del directorio del archivo config
    directory = config['upload_directory']
    
    # Crea el directorio si no existe
    if not os.path.exists(directory):
        os.makedirs(directory)
    
    try:
        # Guarda el archivo en el directorio especificado
        file.save(os.path.join(directory, file.filename))
        return jsonify({"message": "Archivo subido con éxito"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002)
