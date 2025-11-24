from datetime import timedelta
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.database import obtener_bd
from app.modelos import UsuarioAdmin
from app.schemas import Token, UsuarioAdminCrear, UsuarioAdminSalida
from app.security import verificar_clave, obtener_hash_clave, crear_token_acceso, TIEMPO_EXPIRACION_MINUTOS

router = APIRouter(tags=["Autenticación"])

# Dependencia para extraer el token del header Authorization
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

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