from sqlalchemy import create_engine, text
import urllib.parse
import sys

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

# Default to 'postgres' if not provided
SU_PASSWORD = sys.argv[1] if len(sys.argv) > 1 else "postgres"
SU_USER = "postgres"
SERVIDOR_BD = "localhost"
PUERTO_BD = "5432"
NOMBRE_BD = "postgres"

# User to grant permissions TO
USER_TO_GRANT = "antigravity" # In reality this should be read from .env but I know it's the configured user

clave_codificada = urllib.parse.quote_plus(SU_PASSWORD)
URL_BASE_DATOS = f"postgresql://{SU_USER}:{clave_codificada}@{SERVIDOR_BD}:{PUERTO_BD}/{NOMBRE_BD}"

engine = create_engine(URL_BASE_DATOS)

def fix_permissions():
    print(f"Conectando como superusuario '{SU_USER}'...")
    
    commands = [
        f'GRANT USAGE ON SCHEMA encuestas_oltp TO "{USER_TO_GRANT}";',
        f'GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA encuestas_oltp TO "{USER_TO_GRANT}";',
        f'GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA encuestas_oltp TO "{USER_TO_GRANT}";'
    ]
    
    with engine.connect() as conn:
        with conn.begin(): 
            for cmd in commands:
                print(f"Ejecutando: {cmd}")
                conn.execute(text(cmd))
                print("OK.")

if __name__ == "__main__":
    try:
        fix_permissions()
        print("EXITO: Permisos otorgados correctamente.")
    except Exception as e:
        # Handle potential encoding issues when printing exception
        try:
            msg = str(e)
            print(f"FALLO al conectar o ejecutar: {msg}")
        except Exception as inner_e:
             print(f"FALLO al conectar o ejecutar (Error de codificacion: {inner_e})")
        sys.exit(1)
