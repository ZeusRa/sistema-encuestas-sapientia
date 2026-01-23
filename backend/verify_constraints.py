import os
import sys
from dotenv import load_dotenv
from sqlalchemy import create_engine, inspect
import urllib.parse

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
load_dotenv()

# Copy-paste logic from database.py
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
inspector = inspect(engine)

schema = 'encuestas_oltp'
target_tables = ['asignacion_usuario', 'usuario_admin']

for table in target_tables:
    print(f"--- Table: {table} ---")
    cols = inspector.get_columns(table, schema=schema)
    print("Columns:")
    for c in cols:
        print(f"  {c['name']} ({c['type']}) Nullable: {c['nullable']}")
    
    print("Unique Constraints:")
    ucs = inspector.get_unique_constraints(table, schema=schema)
    for uc in ucs:
        print(f"  {uc['name']}: {uc['column_names']}")
