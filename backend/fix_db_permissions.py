from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv
import urllib.parse

load_dotenv()

USUARIO_BD = os.getenv("BD_USUARIO", "postgres")
CLAVE_BD = os.getenv("BD_CLAVE", "")
SERVIDOR_BD = os.getenv("BD_SERVIDOR", "localhost")
PUERTO_BD = os.getenv("BD_PUERTO", "5432")
NOMBRE_BD = os.getenv("BD_NOMBRE", "postgres")

clave_codificada = urllib.parse.quote_plus(CLAVE_BD)
URL_BASE_DATOS = f"postgresql://{USUARIO_BD}:{clave_codificada}@{SERVIDOR_BD}:{PUERTO_BD}/{NOMBRE_BD}"

engine = create_engine(URL_BASE_DATOS)

def fix_permissions():
    user_to_grant = USUARIO_BD
    print(f"Intentando otorgar permisos a: {user_to_grant}")
    
    commands = [
        f'GRANT USAGE ON SCHEMA encuestas_oltp TO "{user_to_grant}";',
        f'GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA encuestas_oltp TO "{user_to_grant}";',
        f'GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA encuestas_oltp TO "{user_to_grant}";'
    ]
    
    with engine.connect() as conn:
        with conn.begin(): # Start transaction
            for cmd in commands:
                print(f"Ejecutando: {cmd}")
                try:
                    conn.execute(text(cmd))
                    print("OK.")
                except Exception as e:
                    print(f"Error ejecutando '{cmd}': {e}")
                    # Don't raise immediately, try others? No, likely all fail if one fails.
                    raise e
                    
    print("\nVerificación: Intentando leer tabla...")
    with engine.connect() as conn:
        res = conn.execute(text("SELECT count(*) FROM encuestas_oltp.usuario_admin"))
        print(f"Lectura exitosa. Count: {res.scalar()}")

if __name__ == "__main__":
    try:
        fix_permissions()
        print("EXITO: Permisos otorgados.")
    except Exception as e:
        print(f"FALLO: No se pudieron otorgar permisos automáticamente. Posiblemente se requiera un superusuario. Error: {e}")
