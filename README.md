Sistema de Encuestas - Sapientia

Este proyecto implementa un sistema de gestión de encuestas desacoplado para la plataforma Sapientia.

Requisitos Previos
Asegúrate de tener instalado en tu máquina:

Python 3.10+
Node.js 18+
PostgreSQL 15+
Git

1. Configuración de Base de Datos
Crea una base de datos en PostgreSQL llamada db_encuestas (o usa postgres).
Ejecuta el script SQL ubicado en database/database_schema.sql usando una herramienta como pgAdmin o DBeaver.
Esto creará los esquemas encuestas_oltp, encuestas_olap y todas las tablas necesarias.

2. Configuración del Backend (API)
Navega a la carpeta del backend:

cd backend

Crea un entorno virtual:

python -m venv venv

Activa el entorno virtual:

Windows: .\venv\Scripts\activate

Instala las dependencias:

pip install -r requerimientos.txt

Configura las variables de entorno:
Copia el archivo .env.example y renómbralo a .env.

Edita .env con tus credenciales de PostgreSQL locales.

BD_USUARIO=postgres
BD_CLAVE=tu_contraseña
BD_NOMBRE=db_encuestas
...

Inicia el servidor:

uvicorn main:app --reload

La API estará disponible en: http://localhost:8000
Documentación Swagger: http://localhost:8000/docs

Usuario Administrador Inicial:
Para poder entrar al sistema, necesitas crear un primer usuario vía API (Swagger):

Ve a POST /usuarios/ en Swagger.

Crea un usuario con rol ADMINISTRADOR (ej: admin / admin123).

3. Configuración del Frontend (Admin)
Abre una nueva terminal y navega a la carpeta frontend:

cd frontend

Instala las dependencias de Node:

npm install


Inicia el servidor de desarrollo:

npm run dev


Abre el navegador en la URL que muestra (usualmente http://localhost:5173).

4. Simulación y ETL
Script ETL: Para mover datos de OLTP a OLAP, ejecuta python etl.py dentro de la carpeta backend (con el entorno virtual activo).




Preparación del Entorno (VS Code)
Python: Extensión oficial de Microsoft. (Para FastAPI, linting, debugging).
ES7+ React/Redux/React-Native snippets: Para agilizar el código en React.
Prettier - Code formatter: Para mantener el código limpio y ordenado automáticamente.
SQLTools (y el driver PostgreSQL): Te permite conectar y consultar tu base de datos PostgreSQL directamente desde VS Code, sin salir del editor.
Thunder Client (o Postman): Para probar tus APIs (GET, POST) dentro de VS Code.


1. Stack Tecnológico Recomendado
Para cumplir con la arquitectura (donde el backend es el núcleo y sirve a múltiples clientes), usamos la siguiente combinación:

A. Base de Datos (Persistencia)
Motor: PostgreSQL (Versión 16).

Por qué: Es el estándar de oro en bases de datos relacionales open source. Soporta nativamente el manejo de esquemas (Schemas), lo cual es vital para nuestra separación física de encuestas_oltp y encuestas_olap dentro de una misma instancia de base de datos. Además, maneja excelente la concurrencia para el CU11.

B. Backend (Servidor de Encuestas)
Lenguaje: Python (3.12.7).
Framework: FastAPI.
ORM (Mapeo Objeto-Relacional): SQLAlchemy (para interactuar con la BD) + Pydantic (para validación de datos).

Por qué FastAPI:
Velocidad: Es uno de los frameworks más rápidos de Python, crítico para el CU11 (Verificar Estado) que no debe añadir latencia a Sapientia.
API-First: Genera automáticamente la documentación (Swagger/OpenAPI), lo cual sirve como el contrato (ISapientiaAPI) que le entregarás al equipo de Sapientia.
Asincronía: Maneja muy bien múltiples conexiones simultáneas.

C. Frontend (Aplicación de Administración)
Framework: React (usando Vite para el scaffolding).
Lenguaje: TypeScript (para mantener la robustez definida en el diseño de objetos).

UI Library: Material UI (MUI) .
Por qué: React es el estándar de la industria. Al ser una SPA (Single Page Application), se desacopla totalmente del backend, consumiendo la IAdminAPI tal como definimos en el diagrama de despliegue. TypeScript asegura que los tipos de datos definidos en el diseño se respeten en el frontend.

D. Proceso ETL (Analítica)
Herramienta: Pandas (Librería de Python).

Ejecución: Celery (para tareas asíncronas) o un simple Cronjob del sistema operativo.
Por qué: Pandas es imbatible para tomar datos, transformarlos (limpieza, agregación) y cargarlos en otro esquema. Es ideal para mover datos de OLTP a OLAP.
Sistema de Encuestas - Sapientia

Este proyecto implementa un sistema de gestión de encuestas desacoplado para la plataforma Sapientia.

Requisitos Previos
Asegúrate de tener instalado en tu máquina:

Python 3.10+
Node.js 18+
PostgreSQL 15+
Git

1. Configuración de Base de Datos
Crea una base de datos en PostgreSQL llamada db_encuestas (o usa postgres).
Ejecuta el script SQL ubicado en database/database_schema.sql usando una herramienta como pgAdmin o DBeaver.

1.1 Crear la base de datos vacía:
CREATE DATABASE db_encuestas;

1.2 Luego, restauran el archivo que les enviaste usando psql:
psql -U postgres -d db_encuestas -f database_full_export.sql


Esto creará los esquemas encuestas_oltp, encuestas_olap y todas las tablas necesarias.

3. Configuración del Backend (API)
Navega a la carpeta del backend:

cd backend

Crea un entorno virtual:

python -m venv venv

Activa el entorno virtual:

Windows: .\venv\Scripts\activate

Instala las dependencias:

pip install -r requerimientos.txt

Configura las variables de entorno:
Copia el archivo .env.example y renómbralo a .env.

Edita .env con tus credenciales de PostgreSQL locales.

BD_USUARIO=postgres
BD_CLAVE=tu_contraseña
BD_NOMBRE=db_encuestas
...

Inicia el servidor:

uvicorn main:app --reload

La API estará disponible en: http://localhost:8000
Documentación Swagger: http://localhost:8000/docs

Usuario Administrador Inicial:
Para poder entrar al sistema, necesitas crear un primer usuario vía API (Swagger):

Ve a POST /usuarios/ en Swagger.

Crea un usuario con rol ADMINISTRADOR (ej: admin / admin123).

3. Configuración del Frontend (Admin)
Abre una nueva terminal y navega a la carpeta frontend:

cd frontend

Instala las dependencias de Node:

npm install


Inicia el servidor de desarrollo:

npm run dev


Abre el navegador en la URL que muestra (usualmente http://localhost:5173).

4. Simulación y ETL
Script ETL: Para mover datos de OLTP a OLAP, ejecuta python etl.py dentro de la carpeta backend (con el entorno virtual activo).
