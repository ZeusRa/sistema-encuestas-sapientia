import os
import urllib.parse
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

URL_BASE_DATOS = os.getenv("DATABASE_URL")
if URL_BASE_DATOS and URL_BASE_DATOS.startswith("postgres://"):
    URL_BASE_DATOS = URL_BASE_DATOS.replace("postgres://", "postgresql://", 1)

engine = create_engine(URL_BASE_DATOS)

# Primero eliminar las opciones asociadas a las preguntas duplicadas
sql_delete_options = """
    DELETE FROM encuestas_oltp.opcion_respuesta
    WHERE id_pregunta IN (
        SELECT id FROM encuestas_oltp.pregunta
        WHERE id_encuesta = 1 AND id NOT IN (
            SELECT MIN(id)
            FROM encuestas_oltp.pregunta
            WHERE id_encuesta = 1
            GROUP BY texto_pregunta
        )
    );
"""

# Luego eliminar las preguntas
sql_cleanup = """
    DELETE FROM encuestas_oltp.pregunta
    WHERE id_encuesta = 1 AND id NOT IN (
        SELECT MIN(id)
        FROM encuestas_oltp.pregunta
        WHERE id_encuesta = 1
        GROUP BY texto_pregunta
    );
"""

with engine.begin() as conn:
    print("Limpiando duplicados en Encuesta 1...")
    
    res_opt = conn.execute(text(sql_delete_options))
    print(f"Opciones eliminadas: {res_opt.rowcount}")

    res = conn.execute(text(sql_cleanup))
    print(f"Preguntas eliminadas: {res.rowcount}")
    
    # Verificar
    count = conn.execute(text("SELECT count(*) FROM encuestas_oltp.pregunta WHERE id_encuesta = 1")).scalar()
    print(f"Preguntas restantes en Encuesta 1: {count}")
