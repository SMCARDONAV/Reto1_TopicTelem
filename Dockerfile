# Usa una imagen base de Python
FROM python:3.12-slim

# Establece el directorio de trabajo en el contenedor
WORKDIR /app

# Copia el archivo requirements.txt al contenedor
COPY requirements.txt .

# Instala las dependencias desde requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copia el resto de los archivos de la aplicación al contenedor
COPY . .

# # Expone el puerto que usará la aplicación
# EXPOSE 8000

# Define el comando por defecto para ejecutar la aplicación
CMD ["python", "main.py"]
