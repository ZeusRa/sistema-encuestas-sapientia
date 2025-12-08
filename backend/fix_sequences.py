from sqlalchemy import text, create_engine
import os
from dotenv import load_dotenv
import urllib.parse

load_dotenv()

URL_BASE_DATOS = os.getenv("DATABASE_URL")
if URL_BASE_DATOS and URL_BASE_DATOS.startswith("postgres://"):
    URL_BASE_DATOS = URL_BASE_DATOS.replace("postgres://", "postgresql://", 1)

if not URL_BASE_DATOS:
    print("DAEMON: No se encontro DATABASE_URL, intentando construirla manualmente...")
    USUARIO_BD = os.getenv("BD_USUARIO", "postgres")
    CLAVE_BD = os.getenv("BD_CLAVE", "")
    SERVIDOR_BD = os.getenv("BD_SERVIDOR", "localhost")
    PUERTO_BD = os.getenv("BD_PUERTO", "5432")
    NOMBRE_BD = os.getenv("BD_NOMBRE", "db_encuestas") 
    clave_codificada = urllib.parse.quote_plus(CLAVE_BD)
    URL_BASE_DATOS = f"postgresql://{USUARIO_BD}:{clave_codificada}@{SERVIDOR_BD}:{PUERTO_BD}/{NOMBRE_BD}"

print(f"Conectando a {URL_BASE_DATOS.split('@')[-1]}")
engine = create_engine(URL_BASE_DATOS)

tablas_a_verificar = [
    ("encuestas_oltp.encuesta", "encuestas_oltp.encuesta_id_seq", "id"),
    ("encuestas_oltp.pregunta", "encuestas_oltp.pregunta_id_seq", "id"),
    ("encuestas_oltp.usuario_admin", "encuestas_oltp.usuario_admin_id_admin_seq", "id_admin"),
]

with engine.connect() as conn:
    conn.execute(text("COMMIT")) # Ensure autocommit mode or handle trans
    for tabla, secuencia, id_col in tablas_a_verificar:
        print(f"--- Revisando {tabla} ---")
        try:
            res_max = conn.execute(text(f"SELECT COALESCE(MAX({id_col}), 0) FROM {tabla}")).scalar()
            res_seq = conn.execute(text(f"SELECT last_value FROM {secuencia}")).scalar()
            
            print(f"  Max ID: {res_max}")
            print(f"  Seq Val: {res_seq}")
            
            if res_seq < res_max:
                print(f"  ⚠ DESFASE DETECTADO en {tabla}. Corrigiendo...")
                # setval to max_id (next val will be max_id + 1 if is_called is true, or max_id if false? generally setval(seq, val) sets current value.)
                # If we setval(seq, max_id), next nextval might be max_id+1.
                # Let's set it to max_id.
                conn.execute(text(f"SELECT setval('{secuencia}', {res_max})"))
                conn.commit()
                print(f"  ✅ Secuencia corregida a {res_max}")
            else:
                print(f"  ✅ Secuencia correcta.")
        except Exception as e:
            print(f"  ❌ Error: {e}")
            conn.rollback()

print("Verificación de secuencias finalizada.")
