import os
import urllib.parse
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

URL_BASE_DATOS = os.getenv("DATABASE_URL")
if URL_BASE_DATOS and URL_BASE_DATOS.startswith("postgres://"):
    URL_BASE_DATOS = URL_BASE_DATOS.replace("postgres://", "postgresql://", 1)

if not URL_BASE_DATOS:
    # Build manually if needed
    pass

engine = create_engine(URL_BASE_DATOS)

with engine.connect() as conn:
    print("--- Preguntas en Encuesta ID 1 ---")
    rows = conn.execute(text("SELECT id, texto_pregunta, orden, activo FROM encuestas_oltp.pregunta WHERE id_encuesta = 1 ORDER BY orden")).fetchall()
    for r in rows:
        print(r)
    
    print(f"\nTotal Preguntas ID 1: {len(rows)}")

    # Check for duplicates based on text/order
    print("\n--- Posibles Duplicados (Mismo Texto) ---")
    sql_dupes = """
        SELECT texto_pregunta, count(*) 
        FROM encuestas_oltp.pregunta 
        WHERE id_encuesta = 1 
        GROUP BY texto_pregunta 
        HAVING count(*) > 1
    """
    dupes = conn.execute(text(sql_dupes)).fetchall()
    for d in dupes:
        print(f"Texto: '{d[0]}' - Cantidad: {d[1]}")
