from sqlalchemy import create_engine, inspect
import os
from dotenv import load_dotenv

load_dotenv()

# Use direct connection string if env vars not perfect, or construct it
# Assuming standard postgres/postgres/localhost/5432/sapientia or similar
# Based on previous tasks, backend has .env. Let's try to load from there or hardcode for local dev
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/sapientia") 

engine = create_engine(DATABASE_URL)
inspector = inspect(engine)

print("Tables in 'sapientia' schema:")
try:
    tables = inspector.get_table_names(schema="sapientia")
    for t in tables:
        print(f" - {t}")
        # Print columns for relevant tables
        if t in ['inscripciones', 'oferta_academica', 'alumnos', 'docentes', 'secciones']:
            print(f"   Columns for {t}:")
            columns = inspector.get_columns(t, schema="sapientia")
            for c in columns:
                print(f"    - {c['name']} ({c['type']})")
except Exception as e:
    print(f"Error inspecting schema: {e}")
