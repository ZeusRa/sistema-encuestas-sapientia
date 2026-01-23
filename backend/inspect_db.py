import os
import sys
from dotenv import load_dotenv
from sqlalchemy import create_engine, inspect
import urllib.parse
import json

# Add backend to sys.path to ensure we can import if needed, though we act standalone
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

load_dotenv()

# Copy-paste logic from database.py to ensure connection
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

try:
    engine = create_engine(URL_BASE_DATOS)
    inspector = inspect(engine)
    
    schemas = inspector.get_schema_names()
    # Filter for relevant schemas
    target_schemas = [s for s in schemas if 'encuestas' in s]
    
    output = {}

    for schema in target_schemas:
        output[schema] = {}
        table_names = inspector.get_table_names(schema=schema)
        for table in table_names:
            output[schema][table] = {
                "columns": [],
                "primary_keys": [],
                "foreign_keys": []
            } # Initialize dict
            
            # Columns
            columns = inspector.get_columns(table, schema=schema)
            for col in columns:
                # Type is an object, convert to string
                col_info = {
                    "name": col['name'],
                    "type": str(col['type']),
                    "nullable": col['nullable'],
                    "default": str(col['default']) if col['default'] else None
                }
                output[schema][table]["columns"].append(col_info)
            
            # PKs
            pks = inspector.get_pk_constraint(table, schema=schema)
            output[schema][table]["primary_keys"] = pks.get('constrained_columns', [])

            # FKs
            fks = inspector.get_foreign_keys(table, schema=schema)
            for fk in fks:
                output[schema][table]["foreign_keys"].append({
                    "constrained_columns": fk['constrained_columns'],
                    "referred_schema": fk['referred_schema'],
                    "referred_table": fk['referred_table'],
                    "referred_columns": fk['referred_columns']
                })
    
    print(json.dumps(output, indent=2))

except Exception as e:
    print(f"Error: {e}")
