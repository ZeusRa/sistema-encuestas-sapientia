import os
import urllib.parse
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

URL_BASE_DATOS = os.getenv("DATABASE_URL")
if URL_BASE_DATOS and URL_BASE_DATOS.startswith("postgres://"):
    URL_BASE_DATOS = URL_BASE_DATOS.replace("postgres://", "postgresql://", 1)

if not URL_BASE_DATOS:
    USUARIO_BD = os.getenv("BD_USUARIO", "postgres")
    CLAVE_BD = os.getenv("BD_CLAVE", "")
    SERVIDOR_BD = os.getenv("BD_SERVIDOR", "localhost")
    PUERTO_BD = os.getenv("BD_PUERTO", "5432")
    NOMBRE_BD = os.getenv("BD_NOMBRE", "db_encuestas") 
    clave_codificada = urllib.parse.quote_plus(CLAVE_BD)
    URL_BASE_DATOS = f"postgresql://{USUARIO_BD}:{clave_codificada}@{SERVIDOR_BD}:{PUERTO_BD}/{NOMBRE_BD}"

engine = create_engine(URL_BASE_DATOS)

with engine.connect() as conn:
    print("Agregando columnas a encuestas_oltp.asignacion_usuario...")
    try:
        conn.execute(text("ALTER TABLE encuestas_oltp.asignacion_usuario ADD COLUMN IF NOT EXISTS metadatos_asignacion JSONB;"))
        conn.execute(text("ALTER TABLE encuestas_oltp.asignacion_usuario ADD COLUMN IF NOT EXISTS id_referencia_contexto VARCHAR(255);"))
        conn.commit()
        print("✅ Columnas agregadas exitosamente.")
    except Exception as e:
        print(f"❌ Error: {e}")
