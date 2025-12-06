from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv
import urllib.parse

load_dotenv()

USUARIO_BD = os.getenv("BD_USUARIO", "postgres")
CLAVE_BD = os.getenv("BD_CLAVE", "")
SERVIDOR_BD = os.getenv("BD_SERVIDOR", "localhost")
PUERTO_BD = os.getenv("BD_PUERTO", "5432")
NOMBRE_BD = os.getenv("BD_NOMBRE", "postgres")

clave_codificada = urllib.parse.quote_plus(CLAVE_BD)
URL_BASE_DATOS = f"postgresql://{USUARIO_BD}:{clave_codificada}@{SERVIDOR_BD}:{PUERTO_BD}/{NOMBRE_BD}"

engine = create_engine(URL_BASE_DATOS)

def test_select():
    with engine.connect() as conn:
        print("Intentando SELECT en encuestas_oltp.encuesta...")
        result = conn.execute(text("SELECT * FROM encuestas_oltp.encuesta LIMIT 1"))
        print(f"Filas: {result.fetchall()}")

if __name__ == "__main__":
    try:
        test_select()
        print("SELECT exitoso.")
    except Exception as e:
        print(f"FALLO SELECT: {e}")
