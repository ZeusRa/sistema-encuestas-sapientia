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