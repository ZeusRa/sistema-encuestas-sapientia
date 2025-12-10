"""
MOTIVO DE LA PRUEBA:
Verificar si existen respuestas asociadas a la encuesta ID 15.
Esto es crucial para determinar si es seguro eliminar preguntas o si se requieren estrategias de migración.

LOGICA DE EJECUCION:
1. Conecta a la base de datos.
2. Cuenta el número total de respuestas en la tabla 'respuesta' asociadas a preguntas de la encuesta 15.
"""
import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

URL_BASE_DATOS = os.getenv("DATABASE_URL")
if URL_BASE_DATOS and URL_BASE_DATOS.startswith("postgres://"):
    URL_BASE_DATOS = URL_BASE_DATOS.replace("postgres://", "postgresql://", 1)

engine = create_engine(URL_BASE_DATOS)

def check_answers(survey_id):
    with engine.connect() as conn:
        count = conn.execute(text(f"""
            SELECT count(*) 
            FROM encuestas_oltp.respuesta r
            JOIN encuestas_oltp.pregunta p ON r.id_pregunta = p.id
            WHERE p.id_encuesta = {survey_id}
        """)).scalar()
        print(f"Respuestas en encuesta {survey_id}: {count}")

if __name__ == "__main__":
    check_answers(15)
