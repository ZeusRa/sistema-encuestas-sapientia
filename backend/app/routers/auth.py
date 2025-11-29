from datetime import timedelta
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.database import obtener_bd
from jose import JWTError, jwt
from app.modelos import UsuarioAdmin
from app.schemas import Token, UsuarioAdminCrear, UsuarioAdminSalida, CambioClave, DatosToken
from app.security import verificar_clave, obtener_hash_clave, crear_token_acceso, TIEMPO_EXPIRACION_MINUTOS, CLAVE_SECRETA, ALGORITMO

router = APIRouter(tags=["Autenticación"])

# Dependencia para extraer el token del header Authorization
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def obtener_usuario_actual(token: str = Depends(oauth2_scheme), bd: Session = Depends(obtener_bd)):
    """
    Decodifica el token JWT y recupera el usuario actual de la base de datos.
    """
    credenciales_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudieron validar las credenciales",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, CLAVE_SECRETA, algorithms=[ALGORITMO])
        nombre_usuario: str = payload.get("sub")
        if nombre_usuario is None:
            raise credenciales_exception
        token_datos = DatosToken(nombre_usuario=nombre_usuario)
    except JWTError:
        raise credenciales_exception

    usuario = bd.query(UsuarioAdmin).filter(UsuarioAdmin.nombre_usuario == token_datos.nombre_usuario).first()
    if usuario is None:
        raise credenciales_exception
    return usuario

@router.post("/token", response_model=Token)
def login_para_token_acceso(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    bd: Session = Depends(obtener_bd)
):
    """
    Endpoint estándar OAuth2 para obtener un token.
    Recibe 'username' y 'password' en form-data.
    """
    # 1. Buscar usuario en la BD
    usuario = bd.query(UsuarioAdmin).filter(UsuarioAdmin.nombre_usuario == form_data.username).first()
    
    # 2. Verificar si existe y si la clave es correcta
    if not usuario or not verificar_clave(form_data.password, usuario.clave_encriptada):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 3. Crear el token
    tiempo_expiracion = timedelta(minutes=TIEMPO_EXPIRACION_MINUTOS)
    token_acceso = crear_token_acceso(
        datos={"sub": usuario.nombre_usuario, "rol": usuario.rol.value},
        tiempo_expiracion=tiempo_expiracion
    )
    
    return {"access_token": token_acceso, "token_type": "bearer"}

@router.post("/usuarios/", response_model=UsuarioAdminSalida, status_code=status.HTTP_201_CREATED)
def crear_usuario_admin(
    usuario: UsuarioAdminCrear, 
    bd: Session = Depends(obtener_bd)
):
    """
    Crea un nuevo usuario administrativo (Admin o Directivo).
    La clave se encripta antes de guardar.
    """
    # Verificar si ya existe
    usuario_existente = bd.query(UsuarioAdmin).filter(UsuarioAdmin.nombre_usuario == usuario.nombre_usuario).first()
    if usuario_existente:
        raise HTTPException(status_code=400, detail="El nombre de usuario ya está registrado")
    
    # Encriptar clave
    clave_hash = obtener_hash_clave(usuario.clave)
    
    # Crear nuevo usuario
    nuevo_usuario = UsuarioAdmin(
        nombre_usuario=usuario.nombre_usuario,
        clave_encriptada=clave_hash,
        rol=usuario.rol
    )
    
    bd.add(nuevo_usuario)
    bd.commit()
    bd.refresh(nuevo_usuario)
    
    return nuevo_usuario

@router.post("/auth/cambiar-clave")
def cambiar_clave(
    datos: CambioClave,
    usuario_actual: UsuarioAdmin = Depends(obtener_usuario_actual),
    bd: Session = Depends(obtener_bd)
):
    """
    Permite al usuario autenticado cambiar su contraseña.
    """
    # 1. Verificar clave actual
    if not verificar_clave(datos.clave_actual, usuario_actual.clave_encriptada):
        raise HTTPException(status_code=400, detail="La contraseña actual es incorrecta")

    # 2. Verificar que las nuevas claves coincidan
    if not datos.claves_coinciden:
        raise HTTPException(status_code=400, detail="Las nuevas contraseñas no coinciden")

    # 3. Actualizar la clave
    nueva_clave_hash = obtener_hash_clave(datos.clave_nueva)
    usuario_actual.clave_encriptada = nueva_clave_hash

    bd.add(usuario_actual)
    bd.commit()

    return {"mensaje": "Contraseña actualizada correctamente"}