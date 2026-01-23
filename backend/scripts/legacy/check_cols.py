import os
import sys
from dotenv import load_dotenv
from sqlalchemy import create_engine, inspect
import urllib.parse

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
load_dotenv()

URL_BASE_DATOS = os.getenv("DATABASE_URL")
if URL_BASE_DATOS:
    if URL_BASE_DATOS.startswith("postgres://"):
        URL_BASE_DATOS = URL_BASE_DATOS.replace("postgres://", "postgresql://", 1)
else:
    # Minimal fallback
    URL_BASE_DATOS = "postgresql://postgres:postgres@localhost:5432/encuestas" # Guessing or relying on env

engine = create_engine(URL_BASE_DATOS)
inspector = inspect(engine)

schema = 'encuestas_oltp'
target_tables = ['encuesta']

for table in target_tables:
    cols = inspector.get_columns(table, schema=schema)
    for c in cols:
        if c['name'] in ['estado', 'prioridad']:
            print(f"Column: {c['name']}, Type: {c['type']}")
