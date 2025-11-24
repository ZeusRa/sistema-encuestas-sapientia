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
    columns = insp.get_columns('encuesta', schema='encuestas_oltp')
    col_names = [c['name'] for c in columns]
    print(f"Columnas en encuesta: {col_names}")
    
    if 'acciones_disparadoras' in col_names and 'configuracion' in col_names:
        print("SUCCESS: Columnas encontradas.")
    else:
        print("FAILURE: Faltan columnas.")
        if 'accion_disparadora' in col_names:
            print("WARNING: Columna antigua 'accion_disparadora' encontrada.")

if __name__ == "__main__":
    try:
        check_columns()
    except Exception as e:
        print(f"Error: {e}")
