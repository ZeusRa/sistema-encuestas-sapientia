from app.database import SesionLocal
from app.modelos import AsignacionUsuario
from app.services import sapientia_service
from sqlalchemy.orm.attributes import flag_modified
import sys

def fix_survey_33_context():
    db = SesionLocal()
    try:
        # Get all assignments for Survey 33
        # Warning: This iterates all assignments. For test data it's fine.
        asignaciones = db.query(AsignacionUsuario).filter(AsignacionUsuario.id_encuesta == 33).all()
        print(f"Found {len(asignaciones)} assignments for Survey 33.")
        
        # We need to map student ID -> Context
        # Fetch clean list of students
        # Note: get_alumnos_cursando might return duplicates if we don't handle it, 
        # but here we just need a lookup map.
        # We'll build a map: id_alumno -> {campus, facultad, carrera}
        
        # Since we can't easily filter get_alumnos_cursando by IDs list efficiently without modifying it,
        # we will fetch all (or filter by generic params if possible).
        # For simplicity in this script, we re-use get_alumnos_cursando but we might process a lot.
        # IF the survey 33 was "Solo Alumnos" (all), fetching all is correct.
        
        print("Fetching student context data...")
        student_map = {}
        for alu in sapientia_service.get_alumnos_cursando(db):
            if alu['id'] not in student_map:
                student_map[alu['id']] = {
                    "campus": alu['campus'],
                    "facultad": alu['facultad'],
                    "carrera": alu['carrera']
                }
        
        print(f"Loaded context for {len(student_map)} students.")
        
        updated_count = 0
        for a in asignaciones:
            ctx = student_map.get(a.id_usuario)
            if ctx:
                meta = a.metadatos_asignacion or {}
                # Update metadata
                meta['campus'] = ctx['campus']
                meta['facultad'] = ctx['facultad']
                meta['carrera'] = ctx['carrera']
                
                a.metadatos_asignacion = meta
                flag_modified(a, "metadatos_asignacion")
                updated_count += 1
            else:
                print(f"Warning: Student {a.id_usuario} not found in current offer.")
        
        db.commit()
        print(f"Updated {updated_count} assignments.")

    except Exception as err:
        db.rollback()
        print(f"Error: {err}")
    finally:
        db.close()

if __name__ == "__main__":
    fix_survey_33_context()
