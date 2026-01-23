from app.database import SesionLocal
from app.services import sapientia_service

def check_catalogs():
    db = SesionLocal()
    try:
        cats = sapientia_service.get_catalogos(db)
        print("Sedes/Campuses available:", cats['sedes'])
        
        # Also check count of students in a campus if any
        if cats['sedes']:
            c = cats['sedes'][0]
            print(f"Checking students in first campus: {c}")
            students = list(sapientia_service.get_alumnos_cursando(db, [{"campo": "campus", "valor": c}]))
            print(f"Found {len(students)} students in {c}")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    check_catalogs()
