import sys
import os
 
# Add parent directory to path to import app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
 
from app.database import motor as engine, SesionLocal as SessionLocal
from sqlalchemy import text, inspect

def inspect_schema():
    print("Inspecting 'sapientia' schema...")
    try:
        insp = inspect(engine)
        schema_names = insp.get_schema_names()
        print(f"Schemas found: {schema_names}")
        
        if 'sapientia' in schema_names:
            tables = insp.get_table_names(schema='sapientia')
            print(f"Tables in 'sapientia' schema: {tables}")
            
            for table in tables:
                print(f"\nTable: {table}")
                columns = insp.get_columns(table, schema='sapientia')
                for col in columns:
                    print(f"  - {col['name']} ({col['type']})")
        else:
            print("Schema 'sapientia' not found.")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    inspect_schema()
