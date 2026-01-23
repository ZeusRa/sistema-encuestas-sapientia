from app.database import SesionLocal
from app.modelos import Encuesta, EstadoEncuesta, AsignacionUsuario
from app.servicios.encuesta_servicio import EncuestaServicio
import sys

def reproduce_issue_38():
    db = SesionLocal()
    try:
        # 1. Duplicate Survey 38
        original_id = 38
        survey = db.query(Encuesta).filter(Encuesta.id == original_id).first()
        if not survey:
            print(f"Error: Survey {original_id} not found.")
            return

        print(f"Duplicating Survey {original_id}...")
        new_survey = EncuestaServicio.duplicar_encuesta(db, original_id, 1) # Admin ID 1
        print(f"Created Survey Copy: {new_survey.id} ({new_survey.nombre})")
        print(f"Status: {new_survey.estado}")
        
        # Check if rules were copied
        print(f"Rules copied: {len(new_survey.reglas)}")
        if new_survey.reglas:
            print(f"Rule 1 Target: {new_survey.reglas[0].publico_objetivo}")
            print(f"Rule 1 Filters: {new_survey.reglas[0].filtros_json}")
        else:
            print("WARNING: No rules copied! This might be the issue.")

        # 2. Publish the new survey
        print(f"Publishing Survey {new_survey.id}...")
        EncuestaServicio.publicar_encuesta(db, new_survey.id, 1)
        db.refresh(new_survey)
        print(f"New Status: {new_survey.estado}")

        # 3. Verify Assignments
        count = db.query(AsignacionUsuario).filter(AsignacionUsuario.id_encuesta == new_survey.id).count()
        print(f"Assignments created: {count}")
        
        if count == 0:
            print("FAILURE REPRODUCED: No assignments were created after publishing.")
        else:
             print("SUCCESS: Assignments were created.")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    reproduce_issue_38()
