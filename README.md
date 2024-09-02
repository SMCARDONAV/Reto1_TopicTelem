# ST0263_1716_2466

## Estudiantes
- **Luisa Polanco** (lmpolanco1@eafit.edu.co)
- **Sara Cardona** (smcardonav@eafit.edu.co)

## Profesor
- **Álvaro Enrique Ospina SanJuan**

## Objetivo
Diseñar e implementar un sistema P2P en el que cada nodo/proceso contenga uno o más microservicios para soportar un sistema de compartición de archivos distribuido y descentralizado.

## Reto 1 - Tópicos Especiales en Telemática, 2024-2

### 1. Breve Descripción de la Actividad
El código implementa un sistema basado en el protocolo de Chord para gestionar una red distribuida de nodos. Utiliza conceptos como la tabla de finger, los identificadores únicos de nodo, y las referencias de predecesor y sucesor para mantener y gestionar la red de manera eficiente. Los métodos para unirse, buscar y actualizar en la red están alineados con el comportamiento esperado en una red Chord.

### 1.1 Aspectos Cumplidos
- Implementación de red estructurada Chord.
- El sistema es distribuido y descentralizado.
- Cada nodo contiene uno o más microservicios.
- Implementación de microservicios para la lógica del servidor (PServidor) y cliente (PCliente).
- Facilita la comunicación entre nodos y la interacción con el servicio (PCliente).
- Permite que cualquier peer acceda a los servicios de otro peer.
- Permite que un peer contacte a otro para iniciar en el sistema y mantener la red.
- Implementación de servicios ECO o dummies para la transferencia de archivos (sin transferencia real).
- Cada microservicio permite comunicaciones simultáneas.
- Implementación de comunicación utilizando gRPC.
- Implementación de consultas para obtener información sobre los archivos en cada nodo.
- Compartición del índice o listado de archivos y su URI.
- Implementación de servicio para la descarga de archivos (DUMMY).
- Implementación de servicio para la carga de archivos (ECO/DUMMY).
- Diferenciación de funcionalidades en distintos microservicios.
- Lectura de un archivo de configuración al iniciar el proceso (Bootstrap).
- Inclusión de dirección IP sobre la que el nodo escuchará (ej., 0.0.0.0) en el archivo de configuración.
- Inclusión del puerto en el que el nodo escuchará (dependiendo del middleware) en el archivo de configuración.
- Inclusión del directorio que el nodo utilizará para listar o buscar archivos en el archivo de configuración.
- Inclusión de URL de un peer o superpeer semilla según el tipo de red P2P en el archivo de configuración.

### 1.2 Aspectos No Cumplidos
- Despliegue en AWS para más de dos nodos.
- No se logró implementar la función de listar y buscar archivos en AWS.

## 2. Información General de Diseño de Alto Nivel
Descripción de la arquitectura, patrones y mejores prácticas utilizadas.

## 3. Descripción del Ambiente de Desarrollo y Técnico
- **Python:** 3.12.5
- **Librerías:**
  - `grpcio`: 2.16.1
  - `grpcio-tools`: 2.16.1
  - `pyyaml`: 6.0

## Cómo se Compila y Ejecuta
1. Clona el repositorio:
   ```bash
   git clone https://github.com/SMCARDONAV/Reto1_TopicTelem.git

2. ubicarse en la carpeta proto y ejecutar los siguientes comandos: python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. node_service.proto y python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. node_service.proto. 
3. Para estos archivos en la linea sea adicionar la palabra from .(punto) al inicio 
![image](https://github.com/user-attachments/assets/ff1c7533-2135-470a-9dfc-dd37b6a53cc9)

## detalles del desarrollo.
El desarrollo se realizó usando comunicación gRPC entre los clientes y servidores. Se procuró hacer una correcta distribución de responsabilidades en las funciones y clases. Se hace uso del algoritmo de Chord DHT para administración de la red de peers los cuales se identifican en la red mediante la combinación del hash que representa su ip y su puerto, de esta forma se puede determinar quien es el predecesor y sucesor que tiene cada uno de ellos al entrar a la red. El punto de entrada siempre es el nodo_1 el cual se identifica con la ip que se le asigne y el puerto 2000. Internamente cada uno de los nodos creados tiene una fuente de archivos especifica la cual no es accesible por otros nodos, esto permite que se haga una correcta localización de recursos para sacarle provecho al algoritmo Chord.  
## detalles técnicos
## descripción y como se configura los parámetros del proyecto (ej: ip, puertos, conexión a bases de datos, variables de ambiente, parámetros, etc)}
La configuración de puertos, ip's y conexiones a datos se hace mediante el archivo de inicialización config.yaml el cual recibe estas variables de la siguiente forma: 

![image](https://github.com/user-attachments/assets/3f352ce7-09c0-41ff-84ff-ab63e4ccb46b)
- ip: donde va a correr el nodo. 
- puerto: donde el programa se va a ejecutar.
- directory: donde se encuentran ubicados los archivos de los nodos.
- seed_url: nodo de inicio, este nodo es el punto de entrada a la red para cualquier otro nodo que quiera unirse. 

## opcionalmente - si quiere mostrar resultados o pantallazos 

## 4. Descripción del ambiente de producción.

En la sesión de instancias se tienes dos creadas llamada nodo_1 y nodo_2
![image](https://github.com/user-attachments/assets/e344d27a-c66d-4613-b62a-4b2c6bcd6936)
IP nodo_1: 34.197.114.29 - puerto: 2000
IP nodo 2: 34.237.50.206 - puerto: 3000
Conectar la instancia nodo_1 y ejecutar el siguiente comando:
docker run --network=p2p_network --ip=34.197.114.29 -i -p 2000:2000 mi-nodo
Conectar la instancia nodo_2 y ejecutar el siguiente comando:
docker run --network=p2p_network --ip=34.237.50.206 -i -p 3000:3000 mi-nodo
Elegir la opción 1 desde el nodo_2
![image](https://github.com/user-attachments/assets/1d037170-b796-4008-9353-46f5b868a3e3)

Deberá aparecer el siguiente mensaje:

![image](https://github.com/user-attachments/assets/47b42659-acb4-4686-bcdd-85f12c15759f)

También se hizo la creación del tercer nodo el cual debia unirse a la red: 

![image](https://github.com/user-attachments/assets/fe079402-1f29-4273-a5d2-5eaaa20ae2a0)

Pero se recibe este error al tratar de hacer una conexión a la red de nodos: 

![image](https://github.com/user-attachments/assets/917f1660-a139-4acb-831e-4f0415b240fc)


## 5. otra información que considere relevante para esta actividad.

## referencias:
https://reactiveprogramming.io/blog/es/estilos-arquitectonicos/p2p![image](https://github.com/user-attachments/assets/7841b04e-c964-464b-91e6-dbe99bd1fa2d)
https://github.com/MNoumanAbbasi/Chord-DHT-for-File-Sharing![image](https://github.com/user-attachments/assets/2d623b6e-d7be-404b-b720-0e337d40854f)
https://www.youtube.com/watch?v=gnchfOojMk4
https://grpc.io/docs/languages/python/quickstart/

