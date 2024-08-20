from indexer import indexer_app
from upload_download_service import upload_service_app, download_service_app
from threading import Thread

def run_indexer():
    indexer_app.run(host='0.0.0.0', port=5001)

def run_upload_service():
    upload_service_app.run(host='0.0.0.0', port=5002)

def run_download_service():
    download_service_app.run(host='0.0.0.0', port=5003)

if __name__ == "__main__":
    Thread(target=run_indexer).start()
    Thread(target=run_upload_service).start()
    Thread(target=run_download_service).start()
