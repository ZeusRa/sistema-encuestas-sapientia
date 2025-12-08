# Sistema de Encuestas - Sapientia

Este proyecto implementa un sistema de gestión de encuestas desacoplado para la plataforma Sapientia, utilizando una arquitectura moderna de microservicios contenerizados.

## 🚀 Inicio Rápido (Recomendado)

Este proyecto está contenerizado con **Docker**. 

### 📋 Requisitos Previos
*   [Docker Desktop](https://www.docker.com/products/docker-desktop) instalado y corriendo.
*   Git.

### 🛠️ Configuración e Instalación

1.  **Clonar el repositorio:**
    ```bash
    git clone <url-del-repositorio>
    cd sistema-encuestas-sapientia
    ```

2.  **Configurar Variables de Entorno (Backend):**
    Navega a la carpeta `backend` y crea un archivo `.env`:
    ```bash
    cd backend
    cp .env.example .env
    ```
    Edita el archivo `.env` con tus credenciales de base de datos (Ej. Neon Postgres):
    ```ini
    DATABASE_URL=postgresql://usuario:password@host/db_encuestas?sslmode=require
    # Opcional si usas DATABASE_URL no necesitas las variables individuales, 
    # pero el sistema soporta ambas formas.
    ```

3.  **Ejecutar con Docker Compose:**
    Desde la raíz del proyecto (donde está `docker-compose.yml`):
    ```bash
    docker-compose up --build
    ```

    *   Esto descargará las imágenes (Python 3.12, Node 22), instalará dependencias y levantará los servicios.
    *   **Backend**: Inicializará automáticamente los esquemas `encuestas_oltp` y `encuestas_olap` si no existen.

4.  **Acceder al Sistema:**
    *   **Frontend (App):** [http://localhost:5173](http://localhost:5173)
    *   **Backend (Documentación API):** [http://localhost:8000/docs](http://localhost:8000/docs)

---

## ✅ Ejecución de Pruebas (Tests)

Para ejecutar las pruebas unitarias y de integración (incluyendo verificación de secuencias) dentro del entorno Docker:

```bash
docker-compose exec backend pytest -v
```

Si deseas ver la salida completa de los prints (útil para debug):
```bash
docker-compose exec backend pytest -v -s
```

---

## 🏗️ Arquitectura y Stack Tecnológico

El sistema sigue una arquitectura donde el backend es el núcleo y sirve a múltiples clientes.

### A. Base de Datos (Persistencia)
*   **Motor:** PostgreSQL 16 (Compatible con Neon DB).

### B. Backend (Servidor de Encuestas)
*   **Lenguaje:** Python 3.12.
*   **Framework:** FastAPI.
*   **ORM:** SQLAlchemy + Pydantic.

### C. Frontend (Aplicación de Administración)
*   **Framework:** React + Vite.
*   **Lenguaje:** TypeScript.
*   **UI Library:** Material UI (MUI).
*   **Entorno:** Node.js 22 (Debian).

### D. Proceso ETL (Analítica)
*   **Herramienta:** Pandas (Python).
*   **Función:** Mueve y transforma datos desde el esquema OLTP hacia OLAP para reportes y dashboards.

---

## 🔧 Solución de Problemas Comunes

*   **Error de conexión a BD:** Verifica que `DATABASE_URL` en `backend/.env` sea correcta y que tu IP esté permitida en Neon/AWS si aplica.
*   **Esquemas faltantes:** Reinicia el contenedor backend (`docker-compose restart backend`). El script de inicio (`main.py`) verifica y crea los esquemas `encuestas_oltp` y `encuestas_olap` al arrancar.
*   **Node/Vite Error:** Si modificas dependencias, ejecuta `docker-compose down -v` para limpiar volúmenes y luego `docker-compose up --build`.
