from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.database import obtener_bd, motor, Base
from app import modelos
from app.routers import auth, admin, sapientia, reportes, permisos, plantillas, admin_tecnico, reportes_avanzados
import os
from datetime import datetime

Base.metadata.create_all(bind=motor)

app = FastAPI(title="Sistema de Encuestas Sapientia")

# Configuración CORS desde variables de entorno
# Formato: "http://localhost:5173,http://localhost:3000"
allowed_origins_env = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173")
origins = [origin.strip() for origin in allowed_origins_env.split(",") if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Permisivo para desarrollo/pruebas
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(admin.router) 
app.include_router(sapientia.router)
app.include_router(reportes.router)
app.include_router(reportes_avanzados.router)
app.include_router(permisos.router)
app.include_router(plantillas.router)

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

@app.get("/salud/sapientia")
def verificar_conexion_sapientia():
    """
    Verifica conectividad con la API de Sapientia externa.
    Útil para monitoreo y troubleshooting de integración.
    """
    sapientia_url = os.getenv("SAPIENTIA_API_URL", "http://localhost:5001")
    
    # NOTA: Implementación simplificada sin requests para evitar dependencia externa
    # En producción, considerar agregar requests a requirements.txt para chequeo real
    return {
        "estado": "configurado",
        "url": sapientia_url,
        "timestamp": datetime.now().isoformat(),
        "nota": "Healthcheck simplificado - considera agregar 'requests' para validación completa"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)