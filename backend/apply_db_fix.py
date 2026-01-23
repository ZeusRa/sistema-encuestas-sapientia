import os
import sys
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
import urllib.parse

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
load_dotenv()

URL_BASE_DATOS = os.getenv("DATABASE_URL")
if URL_BASE_DATOS:
    if URL_BASE_DATOS.startswith("postgres://"):
        URL_BASE_DATOS = URL_BASE_DATOS.replace("postgres://", "postgresql://", 1)
else:
    USUARIO_BD = os.getenv("BD_USUARIO", "postgres")
    CLAVE_BD = os.getenv("BD_CLAVE", "")
    SERVIDOR_BD = os.getenv("BD_SERVIDOR", "localhost")
    PUERTO_BD = os.getenv("BD_PUERTO", "5432")
    NOMBRE_BD = os.getenv("BD_NOMBRE", "postgres")
    clave_codificada = urllib.parse.quote_plus(CLAVE_BD)
    URL_BASE_DATOS = f"postgresql://{USUARIO_BD}:{clave_codificada}@{SERVIDOR_BD}:{PUERTO_BD}/{NOMBRE_BD}"

engine = create_engine(URL_BASE_DATOS)

sql_clean_duplicates = """
DELETE FROM encuestas_oltp.asignacion_usuario a
USING encuestas_oltp.asignacion_usuario b
WHERE a.id < b.id
AND a.id_usuario = b.id_usuario
AND a.id_encuesta = b.id_encuesta
AND (a.id_referencia_contexto IS NOT DISTINCT FROM b.id_referencia_contexto);
"""

sql_add_constraint = """
ALTER TABLE encuestas_oltp.asignacion_usuario
ADD CONSTRAINT uq_usuario_encuesta_contexto 
UNIQUE NULLS NOT DISTINCT (id_usuario, id_encuesta, id_referencia_contexto);
"""

try:
    with engine.begin() as connection:
        print("Cleaning duplicates...")
        connection.execute(text(sql_clean_duplicates))
        print("Duplicates cleaned.")
        
        print("Adding constraint...")
        # Check if constraint exists first to avoid error on re-run
        check_sql = "SELECT 1 FROM pg_constraint WHERE conname = 'uq_usuario_encuesta_contexto'"
        result = connection.execute(text(check_sql)).fetchone()
        if not result:
            connection.execute(text(sql_add_constraint))
            print("Constraint added successfully.")
        else:
            print("Constraint already exists.")
except Exception as e:
    print(f"Error: {e}")
