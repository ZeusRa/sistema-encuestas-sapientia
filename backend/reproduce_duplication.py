from app.database import SesionLocal
from app.modelos import Encuesta, EstadoEncuesta
from app.servicios.encuesta_servicio import EncuestaServicio
import sys

def reproduce_duplication():
    db = SesionLocal()
    try:
        # 1. Find an 'En Curso' survey
        survey = db.query(Encuesta).filter(Encuesta.estado == EstadoEncuesta.en_curso).first()
        if not survey:
            print("No 'En Curso' survey found. Creating one or using ID 34/33 if valid...")
            # Fallback to known IDs if they exist and are suitable, but let's try to query first.
            survey = db.query(Encuesta).filter(Encuesta.id == 33).first()
            if survey:
               print(f"Using Survey 33 (Status: {survey.estado})")
            else:
               print("Survey 33 not found.")
               return

        print(f"Attempting to duplicate Survey {survey.id} (Status: {survey.estado})...")
        
        # 2. Call duplication service
        # Mock user ID 1 (Admin)
        new_survey = EncuestaServicio.duplicar_encuesta(db, survey.id, 1)
        
        print(f"Duplication Successful!")
        print(f"New Survey ID: {new_survey.id}")
        print(f"New Name: {new_survey.nombre}")
        print(f"New Status: {new_survey.estado} (Expected: borrador)")
        
        # 3. Verify Assignments NOT copied
        assignment_count = len(new_survey.asignaciones)
        print(f"Assignments count in new survey: {assignment_count} (Expected: 0)")
        
        if new_survey.estado == EstadoEncuesta.borrador and assignment_count == 0:
            print("TEST PASSED: Backend allows duplication and strips assignments.")
        else:
            print("TEST FAILED: Incorrect state or assignments copied.")

    except Exception as e:
        print(f"TEST FAILED with Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    reproduce_duplication()
