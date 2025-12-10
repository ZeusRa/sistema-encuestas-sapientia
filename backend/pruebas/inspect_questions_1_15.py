"""
MOTIVO DE LA PRUEBA:
Inspeccionar las preguntas de las encuestas ID 1 y ID 15 para visualizar diferencias y duplicados.
Permite comparar la estructura de ambas encuestas antes de realizar correcciones.

LOGICA DE EJECUCION:
1. Conecta a la base de datos.
2. Consulta y lista las preguntas de la encuesta 1.
3. Consulta y lista las preguntas de la encuesta 15, resaltando duplicados de texto.
"""
import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import pandas as pd

load_dotenv()

URL_BASE_DATOS = os.getenv("DATABASE_URL")
if URL_BASE_DATOS and URL_BASE_DATOS.startswith("postgres://"):
    URL_BASE_DATOS = URL_BASE_DATOS.replace("postgres://", "postgresql://", 1)

engine = create_engine(URL_BASE_DATOS)

def inspect_survey(survey_id):
    print(f"\n--- Inspecting Survey {survey_id} ---")
    with engine.connect() as conn:
        # Count questions
        count = conn.execute(text(f"SELECT count(*) FROM encuestas_oltp.pregunta WHERE id_encuesta = {survey_id}")).scalar()
        print(f"Total Questions: {count}")
        
        # Get questions
        sql = f"""
            SELECT id, texto_pregunta, orden
            FROM encuestas_oltp.pregunta 
            WHERE id_encuesta = {survey_id} 
            ORDER BY orden, id
        """
        df = pd.read_sql(sql, conn)
        if not df.empty:
            print(df.to_string())
            
            # Check for duplicates within this survey
            duplicates = df[df.duplicated(subset=['texto_pregunta'], keep=False)]
            if not duplicates.empty:
                print("\nDuplicates found within survey:")
                print(duplicates.sort_values(by='texto_pregunta').to_string())
            else:
                print("\nNo exact text duplicates found within survey.")
        else:
            print("No questions found.")

if __name__ == "__main__":
    inspect_survey(1)
    inspect_survey(15)
