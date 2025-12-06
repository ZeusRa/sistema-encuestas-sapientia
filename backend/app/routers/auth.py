from datetime import timedelta, datetime
from typing import Annotated, List
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.database import obtener_bd
from jose import JWTError, jwt
from app.modelos import UsuarioAdmin, RolAdmin
from app.schemas import (
    Token, UsuarioAdminCrear, UsuarioAdminSalida, CambioClave, DatosToken,
    UsuarioActualizarEstado, UsuarioActualizarRol
)
from app.security import verificar_clave, obtener_hash_clave, crear_token_acceso, TIEMPO_EXPIRACION_MINUTOS, CLAVE_SECRETA, ALGORITMO
from app.servicios.permisos import ServicioPermisos

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
    
    # 3. Validar si está activo
    if not usuario.activo:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario inactivo. Contacte al administrador.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 4. Actualizar último login
    usuario.fecha_ultimo_login = datetime.now()
    bd.add(usuario)
    bd.commit()

    # 5. Calcular Permisos Efectivos
    servicio_permisos = ServicioPermisos(bd)
    lista_permisos = servicio_permisos.obtener_permisos_usuario(usuario.id_admin, usuario.rol)

    # 6. Crear el token (Incluir flag de cambio de clave y permisos)
    tiempo_expiracion = timedelta(minutes=TIEMPO_EXPIRACION_MINUTOS)
    token_acceso = crear_token_acceso(
        datos={
            "sub": usuario.nombre_usuario,
            "rol": usuario.rol.value,
            # "debe_cambiar_clave": usuario.debe_cambiar_clave,
            "permisos": lista_permisos # Nueva claim con la lista de permisos
        },
        tiempo_expiracion=tiempo_expiracion
    )
    
    return {"access_token": token_acceso, "token_type": "bearer"}

@router.post("/usuarios/", response_model=UsuarioAdminSalida, status_code=status.HTTP_201_CREATED)
def crear_usuario_admin(
    usuario: UsuarioAdminCrear, 
    bd: Session = Depends(obtener_bd),
    usuario_actual: UsuarioAdmin = Depends(obtener_usuario_actual)
):
    """
    Crea un nuevo usuario administrativo. Solo Administradores pueden crear.
    """
    if usuario_actual.rol != RolAdmin.ADMINISTRADOR:
        raise HTTPException(status_code=403, detail="No tiene permisos para crear usuarios")

    # Verificar si ya existe
    usuario_existente = bd.query(UsuarioAdmin).filter(UsuarioAdmin.nombre_usuario == usuario.nombre_usuario).first()
    if usuario_existente:
        raise HTTPException(status_code=400, detail="El nombre de usuario ya está registrado")
    
    # Manejo de Clave: Si viene vacía, generamos genérica y obligamos cambio
    clave_inicial = usuario.clave
    debe_cambiar = False

    if not clave_inicial:
        clave_inicial = "temporal123" # Clave Genérica
        debe_cambiar = True

    clave_hash = obtener_hash_clave(clave_inicial)
    
    # Crear nuevo usuario
    nuevo_usuario = UsuarioAdmin(
        nombre_usuario=usuario.nombre_usuario,
        clave_encriptada=clave_hash,
        rol=usuario.rol,
        debe_cambiar_clave=debe_cambiar,
        activo=True
    )
    
    bd.add(nuevo_usuario)
    bd.commit()
    bd.refresh(nuevo_usuario)
    
    return nuevo_usuario

@router.get("/usuarios/", response_model=List[UsuarioAdminSalida])
def listar_usuarios(
    bd: Session = Depends(obtener_bd),
    usuario_actual: UsuarioAdmin = Depends(obtener_usuario_actual)
):
    """Lista todos los usuarios del sistema. Solo Administradores."""
    if usuario_actual.rol != RolAdmin.ADMINISTRADOR:
        raise HTTPException(status_code=403, detail="No tiene permisos para listar usuarios")

    return bd.query(UsuarioAdmin).all()

@router.put("/usuarios/{id_admin}/estado", response_model=UsuarioAdminSalida)
def cambiar_estado_usuario(
    id_admin: int,
    estado: UsuarioActualizarEstado,
    bd: Session = Depends(obtener_bd),
    usuario_actual: UsuarioAdmin = Depends(obtener_usuario_actual)
):
    """Activa o desactiva un usuario. Solo Administradores."""
    if usuario_actual.rol != RolAdmin.ADMINISTRADOR:
        raise HTTPException(status_code=403, detail="No tiene permisos")

    usuario = bd.query(UsuarioAdmin).filter(UsuarioAdmin.id_admin == id_admin).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    usuario.activo = estado.activo
    bd.commit()
    bd.refresh(usuario)
    return usuario

@router.put("/usuarios/{id_admin}/regenerar-clave")
def regenerar_clave_usuario(
    id_admin: int,
    bd: Session = Depends(obtener_bd),
    usuario_actual: UsuarioAdmin = Depends(obtener_usuario_actual)
):
    """Asigna clave genérica y obliga cambio. Solo Administradores."""
    if usuario_actual.rol != RolAdmin.ADMINISTRADOR:
        raise HTTPException(status_code=403, detail="No tiene permisos")

    usuario = bd.query(UsuarioAdmin).filter(UsuarioAdmin.id_admin == id_admin).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    nueva_clave = "temporal123"
    usuario.clave_encriptada = obtener_hash_clave(nueva_clave)
    usuario.debe_cambiar_clave = True

    bd.commit()
    return {"mensaje": f"Clave regenerada a '{nueva_clave}' para el usuario {usuario.nombre_usuario}"}

@router.put("/usuarios/{id_admin}/rol", response_model=UsuarioAdminSalida)
def cambiar_rol_usuario(
    id_admin: int,
    datos: UsuarioActualizarRol,
    bd: Session = Depends(obtener_bd),
    usuario_actual: UsuarioAdmin = Depends(obtener_usuario_actual)
):
    """Cambia el rol de un usuario. Solo Administradores."""
    if usuario_actual.rol != RolAdmin.ADMINISTRADOR:
        raise HTTPException(status_code=403, detail="No tiene permisos")

    usuario = bd.query(UsuarioAdmin).filter(UsuarioAdmin.id_admin == id_admin).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    usuario.rol = datos.rol
    bd.commit()
    bd.refresh(usuario)
    return usuario

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

    # 4. Quitar la marca de cambio obligatorio si la tuviera
    usuario_actual.debe_cambiar_clave = False

    bd.add(usuario_actual)
    bd.commit()

    return {"mensaje": "Contraseña actualizada correctamente"}