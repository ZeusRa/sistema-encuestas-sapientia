import os
import urllib.parse
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

URL_BASE_DATOS = os.getenv("DATABASE_URL")
if URL_BASE_DATOS and URL_BASE_DATOS.startswith("postgres://"):
    URL_BASE_DATOS = URL_BASE_DATOS.replace("postgres://", "postgresql://", 1)

engine = create_engine(URL_BASE_DATOS)

with engine.connect() as conn:
    print("--- Sample Oferta ---")
    rows = conn.execute(text("SELECT cod_asignatura, seccion, campus FROM sapientia.oferta_academica LIMIT 5")).fetchall()
    for r in rows:
        print(r)

    print("\n--- Sample Inscripciones ---")
    rows = conn.execute(text("SELECT cod_asignatura, seccion FROM sapientia.inscripciones LIMIT 5")).fetchall()
    for r in rows:
        print(r)

    print("\n--- Probando JOIN ---")
    sql = """
        SELECT count(*)
        FROM sapientia.inscripciones i
        JOIN sapientia.oferta_academica o ON 
            i.cod_asignatura = o.cod_asignatura AND 
            i.seccion = o.seccion
    """
    c = conn.execute(text(sql)).scalar()
    print(f"Total Matches: {c}")

    print("\n--- Probando Filter Campus Asunción ---")
    sql_filt = """
        SELECT count(*)
        FROM sapientia.inscripciones i
        JOIN sapientia.oferta_academica o ON 
            i.cod_asignatura = o.cod_asignatura AND 
            i.seccion = o.seccion
        WHERE LOWER(o.campus) = LOWER('Campus Asunción')
    """
    c_filt = conn.execute(text(sql_filt)).scalar()
    print(f"Matches Campus Asunción: {c_filt}")
