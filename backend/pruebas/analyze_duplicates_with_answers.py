"""
MOTIVO DE LA PRUEBA:
Analizar la distribución de respuestas en las preguntas duplicadas de la encuesta ID 15.
Esto es necesario para determinar si los duplicados tienen respuestas asociadas y planificar 
la unificación de respuestas antes de eliminar las preguntas redundantes.

LOGICA DE EJECUCION:
1. Conecta a la base de datos.
2. Identifica preguntas duplicadas en la encuesta 15 (mismo texto).
3. Para cada grupo de duplicados, cuenta cuántas respuestas tiene cada ID de pregunta.
4. Muestra un reporte para decidir cuál conservar (la que tenga más respuestas o el ID menor).
"""
import os
import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Cargar variables de entorno desde el directorio padre
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

URL_BASE_DATOS = os.getenv("DATABASE_URL")
if URL_BASE_DATOS and URL_BASE_DATOS.startswith("postgres://"):
    URL_BASE_DATOS = URL_BASE_DATOS.replace("postgres://", "postgresql://", 1)

engine = create_engine(URL_BASE_DATOS)

def analyze_duplicates_answers(survey_id):
    print(f"\n--- Analizando Respuestas en Duplicados de Encuesta {survey_id} ---")
    with engine.connect() as conn:
        # Obtener todas las preguntas de la encuesta
        sql_questions = f"""
            SELECT id, texto_pregunta, orden
            FROM encuestas_oltp.pregunta 
            WHERE id_encuesta = {survey_id} 
            ORDER BY texto_pregunta, id
        """
        df_questions = pd.read_sql(sql_questions, conn)
        
        if df_questions.empty:
            print("No se encontraron preguntas.")
            return

        # Identificar duplicados por texto
        duplicates = df_questions[df_questions.duplicated(subset=['texto_pregunta'], keep=False)]
        
        if duplicates.empty:
            print("No se encontraron duplicados de texto exacto.")
            return
            
        print(f"Encontradas {len(duplicates)} preguntas que son parte de grupos de duplicados.")
        
        duplicate_groups = duplicates.groupby('texto_pregunta')
        
        for text_val, group in duplicate_groups:
            print(f"\nPregunta: '{text_val}'")
            ids = group['id'].tolist()
            ids_str = ",".join(map(str, ids))
            
            # Contar respuestas para estos IDs
            sql_answers = f"""
                SELECT id_pregunta, COUNT(*) as count
                FROM encuestas_oltp.respuesta
                WHERE id_pregunta IN ({ids_str})
                GROUP BY id_pregunta
            """
            df_answers = pd.read_sql(sql_answers, conn)
            
            # Combinar info
            merged = pd.merge(group, df_answers, left_on='id', right_on='id_pregunta', how='left')
            merged['count'] = merged['count'].fillna(0).astype(int)
            
            print(merged[['id', 'orden', 'count']].to_string(index=False))

if __name__ == "__main__":
    analyze_duplicates_answers(15)
