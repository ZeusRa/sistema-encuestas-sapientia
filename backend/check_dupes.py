import sys
import os
from sqlalchemy import text

# Add current directory to sys.path to ensure we can import 'app'
sys.path.append(os.getcwd())

from app.database import SesionLocal
from app import modelos

def check_duplicates():
    db = SesionLocal()
    try:
        print("Connected to DB. Checking for duplicate questions...")
        
        # Query for duplicates based on text and survey ID
        sql = text("""
            SELECT id_encuesta, texto_pregunta, COUNT(*) as count
            FROM encuestas_oltp.pregunta
            GROUP BY id_encuesta, texto_pregunta
            HAVING COUNT(*) > 1
        """)
        
        duplicates = db.execute(sql).fetchall()
        
        if not duplicates:
            print("No duplicates found.")
            return

        print(f"Found {len(duplicates)} sets of duplicates:")
        for dup in duplicates:
            print(f"  Survey {dup.id_encuesta}: '{dup.texto_pregunta}' (Count: {dup.count})")
            
            # Find the IDs
            ids_sql = text("SELECT id FROM encuestas_oltp.pregunta WHERE id_encuesta = :eid AND texto_pregunta = :txt ORDER BY id")
            ids = db.execute(ids_sql, {"eid": dup.id_encuesta, "txt": dup.texto_pregunta}).fetchall()
            id_list = [r.id for r in ids]
            print(f"    IDs: {id_list}")

            # Delete duplicates (keep the FIRST one)
            ids_to_delete = id_list[1:]
            if ids_to_delete:
                print(f"    Deleting IDs: {ids_to_delete}")
                db.execute(text("DELETE FROM encuestas_oltp.pregunta WHERE id IN :ids"), {"ids": tuple(ids_to_delete)})
                db.commit() # Uncommented to enable deletion

    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    check_duplicates()
