# apply_schema_update.py
from sqlalchemy import text
from app.database import SesionLocal
import sys

# Encoding safe output
sys.stdout.reconfigure(encoding='utf-8')

def apply_update():
    print("Iniciando actualización de esquema...")
    try:
        db = SesionLocal()
        with open("update_schema_2.sql", "r") as f:
            sql_script = f.read()
        
        # Split by statements if needed, but text() might handle it or we exec one by one
        statements = [s.strip() for s in sql_script.split(';') if s.strip()]
        
        for stmt in statements:
            print(f"Ejecutando: {stmt[:50]}...")
            db.execute(text(stmt))
        
        db.commit()
        print("EXITO: Esquema actualizado correctamente.")
    except Exception as e:
        print(f"ERROR: {str(e)}")
        # Rollback handled by session context usually, but explicit here if needed
        # db.rollback() 
    finally:
        db.close()

if __name__ == "__main__":
    apply_update()
