import os
import urllib.parse
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# 1. Cargar las variables del archivo .env
load_dotenv()

# 2. Obtener credenciales (Variables en Castellano)
# Priorizar DATABASE_URL para despliegues o Docker
URL_BASE_DATOS = os.getenv("DATABASE_URL")

if URL_BASE_DATOS:
    # "Fix" para SQLAlchemy (Dialect)
    if URL_BASE_DATOS.startswith("postgres://"):
        URL_BASE_DATOS = URL_BASE_DATOS.replace("postgres://", "postgresql://", 1)
else:
    # Fallback a variables individuales (local sin docker o legacy)
    USUARIO_BD = os.getenv("BD_USUARIO", "postgres")
    CLAVE_BD = os.getenv("BD_CLAVE", "")
    SERVIDOR_BD = os.getenv("BD_SERVIDOR", "localhost")
    PUERTO_BD = os.getenv("BD_PUERTO", "5432")
    NOMBRE_BD = os.getenv("BD_NOMBRE", "postgres")

    # 3. Codificar la clave para caracteres especiales
    clave_codificada = urllib.parse.quote_plus(CLAVE_BD)

    # 4. Construir URL
    URL_BASE_DATOS = f"postgresql://{USUARIO_BD}:{clave_codificada}@{SERVIDOR_BD}:{PUERTO_BD}/{NOMBRE_BD}"

# Crear el motor de conexión
motor = create_engine(URL_BASE_DATOS)

# Crear clase de Sesión
SesionLocal = sessionmaker(autocommit=False, autoflush=False, bind=motor)

# Clase base para modelos
Base = declarative_base()

# Dependencia para obtener la sesión de BD
def obtener_bd():
    bd = SesionLocal()
    try:
        yield bd
    finally:
        bd.close()