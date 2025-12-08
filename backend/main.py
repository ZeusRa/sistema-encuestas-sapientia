from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.database import obtener_bd, motor, Base
from app import modelos
from app.routers import auth, admin, sapientia, reportes, permisos, plantillas, catalogos, admin_tecnico

# Crear esquema si no existe
with motor.connect() as connection:
    connection.execute(text("CREATE SCHEMA IF NOT EXISTS encuestas_oltp"))
    connection.execute(text("CREATE SCHEMA IF NOT EXISTS encuestas_olap"))
    connection.commit()

Base.metadata.create_all(bind=motor)

app = FastAPI(
    title="Sistema de Encuestas API",
    description="Backend para la gestión de encuestas y bloqueo de inscripciones de Sapientia.",
    version="1.0.0"
)

# --- CONFIGURACIÓN CORS ---
# Permitir que el frontend (React) hable con el backend
origins = [
    "http://localhost:5173",      # Vite default
    "http://127.0.0.1:5173",
    "http://localhost:3000",      # React clásico
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,        # Qué dominios pueden conectar
    allow_credentials=True,
    allow_methods=["*"],          # Permitir todos los métodos (GET, POST, etc.)
    allow_headers=["*"],          # Permitir todos los headers
)
# ---------------------------

app.include_router(auth.router)
app.include_router(admin.router) 
app.include_router(sapientia.router)
app.include_router(reportes.router)
app.include_router(permisos.router)
app.include_router(plantillas.router)
app.include_router(catalogos.router)
app.include_router(admin_tecnico.router)

@app.get("/")
def leer_raiz():
    return {"mensaje": "El Sistema está en línea"}

@app.get("/salud/bd")
def verificar_conexion_bd(bd: Session = Depends(obtener_bd)):
    """
    Verifica si la conexión a PostgreSQL es exitosa ejecutando una consulta simple.
    """
    try:
        # Ejecutamos consulta simple
        resultado = bd.execute(text("SELECT 1"))
        return {
            "estado": "conectado", 
            "motor": "PostgreSQL", 
            "prueba_exitosa": resultado.scalar()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error conectando a la BD: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)