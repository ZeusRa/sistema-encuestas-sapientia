from app.database import SesionLocal
from app.modelos import Pregunta
from sqlalchemy.orm.attributes import flag_modified
import sys
import json

def fix_survey_34():
    db = SesionLocal()
    try:
        # Q5135 is the matrix question in Survey 34
        q = db.query(Pregunta).filter(Pregunta.id == 5135).first()
        if not q:
            print("Question 5135 not found")
            return

        print(f"Before: {q.configuracion_json}")
        
        new_config = q.configuracion_json or {}
        new_config['filas'] = [
            {"texto": "Biblioteca", "orden": 1},
            {"texto": "Cafetería", "orden": 2},
            {"texto": "Laboratorios", "orden": 3}
        ]
        new_config['columnas'] = [
            {"texto": "Malo", "orden": 1},
            {"texto": "Regular", "orden": 2},
            {"texto": "Bueno", "orden": 3},
            {"texto": "Excelente", "orden": 4}
        ]
        
        q.configuracion_json = new_config
        flag_modified(q, "configuracion_json") # Ensure SQLAlchemy detects JSON update
        
        db.commit()
        db.refresh(q)
        print(f"After: {q.configuracion_json}")
        print("Update Successful.")

    except Exception as err:
        db.rollback()
        print(f"Error: {err}")
    finally:
        db.close()

if __name__ == "__main__":
    fix_survey_34()
