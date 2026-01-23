import sys
import os

# Add parent directory to path to import app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import obtener_bd
from app.routers.sapientia import get_catalogo_generico

def verify_catalogos():
    print("Verifying Catalog Endpoints through sapientia.py...")
    
    # Mocking DB session (calling the generator to get the session)
    db_gen = obtener_bd()
    db = next(db_gen)
    
    try:
        catalogs = ["campus", "facultad", "departamento", "carrera", "docente", "asignatura"]
        
        for cat in catalogs:
            print(f"\nTesting '{cat}'...")
            results = get_catalogo_generico(cat, bd=db)
            print(f"Results type: {type(results)}")
            print(f"Count: {len(results)}")
            if len(results) > 0:
                print(f"First item: {results[0]}")
            else:
                print("WARNING: Empty results (might be expected if DB is empty, but verify schema)")
                
        print("\nVerification Complete.")
        
    except Exception as e:
        print(f"ERROR: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    verify_catalogos()
