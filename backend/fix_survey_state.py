from app.database import SesionLocal as SessionLocal
from app.modelos import Encuesta, EstadoEncuesta, PrioridadEncuesta
from datetime import datetime, timedelta

def fix_survey():
    db = SessionLocal()
    try:
        e = db.query(Encuesta).filter(Encuesta.id == 25).first()
        if not e:
            print("Survey 25 not found")
            return

        print(f"Current state: {e.estado}")
        e.estado = EstadoEncuesta.en_curso
        e.fecha_inicio = datetime.now() - timedelta(days=1)
        e.fecha_fin = datetime.now() + timedelta(days=30)
        e.prioridad = PrioridadEncuesta.obligatoria
        e.activo = True
        
        # Ensure it has questions?
        print(f"Preguntas: {len(e.preguntas)}")
        
        db.commit()
        print("Survey 25 updated to EN_CURSO with valid dates.")
    except Exception as ex:
        print(f"Error: {ex}")
    finally:
        db.close()

if __name__ == "__main__":
    fix_survey()
