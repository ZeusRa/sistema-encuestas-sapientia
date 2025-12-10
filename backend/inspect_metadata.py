from app.database import SesionLocal as SessionLocal
from app import modelos
from sqlalchemy import text

db = SessionLocal()

try:
    asignacion = db.query(modelos.AsignacionUsuario).order_by(modelos.AsignacionUsuario.fecha_asignacion.desc()).first()
    
    if asignacion:
        print(f"ID: {asignacion.id}")
        print(f"Ref Contexto: {asignacion.id_referencia_contexto}")
    else:
        print("No se encontraron asignaciones.")

except Exception as e:
    print(f"Error: {e}")
finally:
    db.close()
