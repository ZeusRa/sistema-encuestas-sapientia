from sqlalchemy import create_engine, text, inspect
import os
from dotenv import load_dotenv
import urllib.parse

# Cargar variables
load_dotenv()

USUARIO_BD = os.getenv("BD_USUARIO", "postgres")
CLAVE_BD = os.getenv("BD_CLAVE", "")
SERVIDOR_BD = os.getenv("BD_SERVIDOR", "localhost")
PUERTO_BD = os.getenv("BD_PUERTO", "5432")
NOMBRE_BD = os.getenv("BD_NOMBRE", "postgres")

clave_codificada = urllib.parse.quote_plus(CLAVE_BD)
URL_BASE_DATOS = f"postgresql://{USUARIO_BD}:{clave_codificada}@{SERVIDOR_BD}:{PUERTO_BD}/{NOMBRE_BD}"

engine = create_engine(URL_BASE_DATOS)

def check_columns():
    insp = inspect(engine)
    tables = ['usuario_admin', 'encuesta', 'pregunta', 'opcion_respuesta', 'transaccion_encuesta', 'asignacion_usuario', 'permiso', 'rol_permiso', 'usuario_permiso']
    for t in tables:
        try:
            columns = insp.get_columns(t, schema='encuestas_oltp')
            col_names = sorted([c['name'] for c in columns])
            print(f"--- TABLE: {t} ---")
            print(f"Columns: {col_names}")
        except Exception as e:
            print(f"Error inspecting {t}: {e}")

if __name__ == "__main__":
    try:
        check_columns()
    except Exception as e:
        print(f"Error: {e}")
