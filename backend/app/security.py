from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
import os
from dotenv import load_dotenv

load_dotenv()

# Configuración
CLAVE_SECRETA = os.getenv("CLAVE_SECRETA", "clave_secreta_por_defecto_muy_insegura")
ALGORITMO = "HS256"
TIEMPO_EXPIRACION_MINUTOS = 30

# Contexto para hashing de contraseñas (bcrypt)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verificar_clave(clave_plana: str, clave_encriptada: str) -> bool:
    """Verifica si una contraseña plana coincide con el hash guardado."""
    return pwd_context.verify(clave_plana, clave_encriptada)

def obtener_hash_clave(clave: str) -> str:
    """Genera un hash seguro de la contraseña."""
    if len(clave.encode('utf-8')) > 72:
        raise ValueError("La contraseña es demasiado larga (máximo 72 caracteres)")
    return pwd_context.hash(clave)

def crear_token_acceso(datos: dict, tiempo_expiracion: Optional[timedelta] = None) -> str:
    """Crea un token JWT con datos del usuario y tiempo de expiración."""
    datos_a_codificar = datos.copy()
    if tiempo_expiracion:
        expiracion = datetime.utcnow() + tiempo_expiracion
    else:
        expiracion = datetime.utcnow() + timedelta(minutes=15)
    
    datos_a_codificar.update({"exp": expiracion})
    token_jwt = jwt.encode(datos_a_codificar, CLAVE_SECRETA, algorithm=ALGORITMO)
    return token_jwt