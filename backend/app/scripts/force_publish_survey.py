
import sys
import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Add parent directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from app.database import URL_BASE_DATOS

def force_publish(survey_id):
    print(f"Connecting to database...")
    engine = create_engine(URL_BASE_DATOS)
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        print(f"Updating survey {survey_id} status to 'en_curso'...")
        # Check current status
        result = session.execute(text("SELECT id, nombre, estado FROM encuestas_oltp.encuesta WHERE id = :id"), {"id": survey_id}).fetchone()
        if not result:
            print(f"Survey {survey_id} not found!")
            return

        print(f"Current state: {result.nombre} - {result.estado}")

        # Update
        session.execute(text("UPDATE encuestas_oltp.encuesta SET estado = 'en_curso' WHERE id = :id"), {"id": survey_id})
        session.commit()

        # Verify
        result = session.execute(text("SELECT id, nombre, estado FROM encuestas_oltp.encuesta WHERE id = :id"), {"id": survey_id}).fetchone()
        print(f"New state: {result.nombre} - {result.estado}")

    except Exception as e:
        session.rollback()
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        sid = int(sys.argv[1])
        force_publish(sid)
    else:
        print("Usage: python force_publish_survey.py <survey_id>")
