import os
import urllib.parse
from sqlalchemy import create_engine, text, inspect
from dotenv import load_dotenv

# Reutilizar logica de conexion para asegurar que probamos lo mismo que la app
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
    NOMBRE_BD = os.getenv("BD_NOMBRE", "postgres")
    clave_codificada = urllib.parse.quote_plus(CLAVE_BD)
    URL_BASE_DATOS = f"postgresql://{USUARIO_BD}:{clave_codificada}@{SERVIDOR_BD}:{PUERTO_BD}/{NOMBRE_BD}"

print(f"DAEMON: Conectando a... {URL_BASE_DATOS.split('@')[-1]}") # Log seguro

try:
    engine = create_engine(URL_BASE_DATOS)
    inspector = inspect(engine)

    with engine.connect() as connection:
        # 1. Verificar Nombre de BD y Usuario Actual
        res = connection.execute(text("SELECT current_database(), current_user, version()"))
        db_info = res.fetchone()
        print(f"\n[INFO CONEXION]")
        print(f"DATABASE: {db_info[0]}")
        print(f"USER:     {db_info[1]}")
        print(f"VERSION:  {db_info[2]}")

        # 2. Listar TODOS los esquemas
        print(f"\n[ESQUEMAS ENCONTRADOS]")
        schemas = inspector.get_schema_names()
        print(schemas)
        
        expected_schemas = ["encuestas_oltp", "encuestas_olap"]
        for es in expected_schemas:
            if es not in schemas:
                print(f"❌ ALERTA: Esquema '{es}' NO existe en esta BD.")
            else:
                print(f"✅ Esquema '{es}' encontrado.")

        # 3. Listar Tablas por Esquema
        for es in expected_schemas:
            if es in schemas:
                print(f"\n[TABLAS EN SCHEMA: {es}]")
                tables = inspector.get_table_names(schema=es)
                if not tables:
                    print("  (Ninguna tabla encontrada)")
                for table in tables:
                    print(f"  - {table}")

except Exception as e:
    print(f"\n❌ ERROR CRITICO DE CONEXION: {e}")
