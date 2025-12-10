import os
import urllib.parse
from sqlalchemy import create_engine, inspect
from dotenv import load_dotenv

load_dotenv()

URL_BASE_DATOS = os.getenv("DATABASE_URL")
if URL_BASE_DATOS and URL_BASE_DATOS.startswith("postgres://"):
    URL_BASE_DATOS = URL_BASE_DATOS.replace("postgres://", "postgresql://", 1)

if not URL_BASE_DATOS:
    USUARIO_BD = os.getenv("BD_USUARIO", "postgres")
    CLAVE_BD = os.getenv("BD_CLAVE", "")
    SERVIDOR_BD = os.getenv("BD_SERVIDOR", "localhost")
    PUERTO_BD = os.getenv("BD_PUERTO", "5432")
    NOMBRE_BD = os.getenv("BD_NOMBRE", "db_encuestas")
    clave_codificada = urllib.parse.quote_plus(CLAVE_BD)
    URL_BASE_DATOS = f"postgresql://{USUARIO_BD}:{clave_codificada}@{SERVIDOR_BD}:{PUERTO_BD}/{NOMBRE_BD}"

engine = create_engine(URL_BASE_DATOS)
inspector = inspect(engine)

print("\n--- Columnas en sapientia.oferta_academica ---")
try:
    for col in inspector.get_columns("oferta_academica", schema="sapientia"):
        print(f"  - {col['name']} ({col['type']})")
except Exception as e:
    print(f"Error inspeccionando tabla: {e}")
