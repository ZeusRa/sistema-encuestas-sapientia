import os
import sys
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
import urllib.parse
import hashlib

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
load_dotenv()

# Setup DB connection
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

def verify_db_constraint():
    print("\n--- Verifying Unique Constraint ---")
    # Try to insert duplicate assignment (assuming user 1, survey 1 exists or can be used)
    # We'll just check if the constraint exists in postgres metadata
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1 FROM pg_constraint WHERE conname = 'uq_usuario_encuesta_contexto'")).fetchone()
        if result:
            print("✅ Constraint 'uq_usuario_encuesta_contexto' exists.")
        else:
            print("❌ Constraint MISSING.")

def verify_hashing_logic():
    print("\n--- Verifying Hashing Logic (Simulation) ---")
    # We can't easily check the live endpoint without running the whole app, but we can verify the same logic produces the hash.
    id_user = 123
    salt = "SAPIENTIA_SECRET_SALT_2025"
    expected_hash = hashlib.sha256(f"{id_user}{salt}".encode()).hexdigest()
    
    # We assume the code change in sapientia.py is applied (we verify strict text match)
    with open("app/routers/sapientia.py", "r", encoding="utf-8") as f:
        content = f.read()
        if 'hashlib.sha256' in content and 'SAPIENTIA_SECRET_SALT_2025' in content:
             print("✅ Hashing logic found in code.")
        else:
             print("❌ Hashing logic NOT found in code.")

def verify_blocking_logic():
    print("\n--- Verifying Blocking Logic (Static Analysis) ---")
    with open("app/routers/sapientia.py", "r", encoding="utf-8") as f:
        content = f.read()
        if 'mod.Encuesta.prioridad == mod.PrioridadEncuesta.obligatoria' in content:
             print("✅ Priority check found in code.")
        else:
             print("❌ Priority check NOT found in code.")

if __name__ == "__main__":
    verify_db_constraint()
    verify_hashing_logic()
    verify_blocking_logic()
