from typing import List, Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import obtener_bd
from app import modelos, schemas
from app.routers.auth import oauth2_scheme # Para proteger las rutas
from jose import JWTError, jwt
from app.security import CLAVE_SECRETA, ALGORITMO

router = APIRouter(
    prefix="/admin",
    tags=["Administración de Encuestas"]
)

# Dependencia para obtener el usuario actual desde el token
def obtener_usuario_actual(token: Annotated[str, Depends(oauth2_scheme)], bd: Session = Depends(obtener_bd)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudieron validar las credenciales",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, CLAVE_SECRETA, algorithms=[ALGORITMO])
        username: str = payload.get("sub")
        rol: str = payload.get("rol")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
        
    # Opcional: Verificar que el usuario exista en BD si se requiere más seguridad
    # Por ahora confiamos en el token para velocidad
    return {"username": username, "rol": rol}

# Dependencia para verificar que sea ADMINISTRADOR
def solo_administradores(usuario_actual: dict = Depends(obtener_usuario_actual)):
    if usuario_actual["rol"] != "ADMINISTRADOR":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos de administrador"
        )
    return usuario_actual

# --- ENDPOINTS ---

@router.post("/encuestas/", response_model=schemas.EncuestaSalida, status_code=status.HTTP_201_CREATED)
def crear_encuesta_completa(encuesta: schemas.EncuestaCrear, bd: Session = Depends(obtener_bd), usuario: dict = Depends(solo_administradores)):
    acciones = [a.value for a in encuesta.acciones_disparadoras]
    nueva_encuesta = modelos.Encuesta(
        nombre=encuesta.nombre, descripcion=encuesta.descripcion, mensaje_final=encuesta.mensaje_final, fecha_inicio=encuesta.fecha_inicio, fecha_fin=encuesta.fecha_fin,
        prioridad=encuesta.prioridad, acciones_disparadoras=acciones, configuracion=encuesta.configuracion,
        estado=modelos.EstadoEncuesta.borrador, activo=encuesta.activo
    )
    bd.add(nueva_encuesta)
    bd.flush()
    for regla in encuesta.reglas:
        nueva_regla = modelos.ReglaAsignacion(id_encuesta=nueva_encuesta.id, id_facultad=regla.id_facultad, id_carrera=regla.id_carrera, id_asignatura=regla.id_asignatura, publico_objetivo=regla.publico_objetivo)
        bd.add(nueva_regla)
    for preg in encuesta.preguntas:
        crear_pregunta_con_opciones(bd, nueva_encuesta.id, preg)
    bd.commit()
    bd.refresh(nueva_encuesta)
    return nueva_encuesta

# Dependencia para obtener el usuario actual desde el token
def obtener_usuario_actual(token: Annotated[str, Depends(oauth2_scheme)], bd: Session = Depends(obtener_bd)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudieron validar las credenciales",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, CLAVE_SECRETA, algorithms=[ALGORITMO])
        username: str = payload.get("sub")
        rol: str = payload.get("rol")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
        
    # Opcional: Verificar que el usuario exista en BD si se requiere más seguridad
    # Por ahora confiamos en el token para velocidad
    return {"username": username, "rol": rol}

# Dependencia para verificar que sea ADMINISTRADOR
def solo_administradores(usuario_actual: dict = Depends(obtener_usuario_actual)):
    if usuario_actual["rol"] != "ADMINISTRADOR":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos de administrador"
        )
    return usuario_actual

# --- ENDPOINTS ---

@router.get("/encuestas/", response_model=List[schemas.EncuestaSalida])
def listar_encuestas(skip: int = 0, limit: int = 100, bd: Session = Depends(obtener_bd), usuario: dict = Depends(obtener_usuario_actual)):
    encuestas = bd.query(modelos.Encuesta).offset(skip).limit(limit).all()
    return encuestas

@router.get("/encuestas/{encuesta_id}", response_model=schemas.EncuestaSalida)
def obtener_encuesta(encuesta_id: int, bd: Session = Depends(obtener_bd), usuario: dict = Depends(obtener_usuario_actual)):
    encuesta = bd.query(modelos.Encuesta).filter(modelos.Encuesta.id == encuesta_id).first()
    if not encuesta: raise HTTPException(status_code=404, detail="Encuesta no encontrada")
    return encuesta

@router.put("/encuestas/{encuesta_id}", response_model=schemas.EncuestaSalida)
def actualizar_encuesta(encuesta_id: int, encuesta_actualizada: schemas.EncuestaCrear, bd: Session = Depends(obtener_bd), usuario: dict = Depends(solo_administradores)):
    db_encuesta = bd.query(modelos.Encuesta).filter(modelos.Encuesta.id == encuesta_id).first()
    if not db_encuesta: raise HTTPException(status_code=404, detail="Encuesta no encontrada")
    if db_encuesta.estado != modelos.EstadoEncuesta.borrador and encuesta_actualizada.estado == modelos.EstadoEncuesta.borrador: pass
    
    db_encuesta.nombre = encuesta_actualizada.nombre
    db_encuesta.descripcion = encuesta_actualizada.descripcion
    db_encuesta.mensaje_final = encuesta_actualizada.mensaje_final
    db_encuesta.fecha_inicio = encuesta_actualizada.fecha_inicio
    db_encuesta.fecha_fin = encuesta_actualizada.fecha_fin
    db_encuesta.prioridad = encuesta_actualizada.prioridad
    db_encuesta.acciones_disparadoras = [a.value for a in encuesta_actualizada.acciones_disparadoras]
    db_encuesta.configuracion = encuesta_actualizada.configuracion
    db_encuesta.activo = encuesta_actualizada.activo
    
    db_encuesta.reglas = []
    db_encuesta.preguntas = []
    bd.flush()
    for regla in encuesta_actualizada.reglas:
        nueva_regla = modelos.ReglaAsignacion(id_encuesta=encuesta_id, id_facultad=regla.id_facultad, id_carrera=regla.id_carrera, id_asignatura=regla.id_asignatura, publico_objetivo=regla.publico_objetivo)
        bd.add(nueva_regla)
    for preg in encuesta_actualizada.preguntas:
        crear_pregunta_con_opciones(bd, encuesta_id, preg)
    bd.commit()
    bd.refresh(db_encuesta)
    return db_encuesta

def crear_pregunta_con_opciones(bd: Session, id_encuesta: int, preg: schemas.PreguntaCrear):
    nueva_pregunta = modelos.Pregunta(id_encuesta=id_encuesta, texto_pregunta=preg.texto_pregunta, orden=preg.orden, tipo=preg.tipo, configuracion_json=preg.configuracion_json, activo=preg.activo)
    bd.add(nueva_pregunta)
    bd.flush()
    for opc in preg.opciones:
        nueva_opcion = modelos.OpcionRespuesta(id_pregunta=nueva_pregunta.id, texto_opcion=opc.texto_opcion, orden=opc.orden)
        bd.add(nueva_opcion)
    bd.commit()
    bd.refresh(nueva_pregunta)
    return nueva_pregunta

@router.post("/encuestas/{encuesta_id}/publicar", response_model=schemas.EncuestaSalida)
def publicar_encuesta(
    encuesta_id: int,
    bd: Session = Depends(obtener_bd),
    usuario: dict = Depends(solo_administradores)
):
    """
    Cambia el estado de BORRADOR a EN_CURSO.
    """
    encuesta = bd.query(modelos.Encuesta).filter(modelos.Encuesta.id == encuesta_id).first()
    if not encuesta:
        raise HTTPException(status_code=404, detail="Encuesta no encontrada")
    
    if encuesta.estado != modelos.EstadoEncuesta.borrador:
        raise HTTPException(status_code=400, detail="Solo se pueden publicar encuestas en estado BORRADOR")

    encuesta.estado = modelos.EstadoEncuesta.en_curso
    bd.commit()
    bd.refresh(encuesta)
    return encuesta

@router.post("/encuestas/{encuesta_id}/finalizar", response_model=schemas.EncuestaSalida)
def finalizar_encuesta(
    encuesta_id: int,
    bd: Session = Depends(obtener_bd),
    usuario: dict = Depends(solo_administradores)
):
    """
    Cambia el estado a FINALIZADO.
    """
    encuesta = bd.query(modelos.Encuesta).filter(modelos.Encuesta.id == encuesta_id).first()
    if not encuesta:
        raise HTTPException(status_code=404, detail="Encuesta no encontrada")
    
    # CORREGIDO: Usar 'finalizado'
    if encuesta.estado == modelos.EstadoEncuesta.finalizado:
        raise HTTPException(status_code=400, detail="La encuesta ya está finalizada")

    encuesta.estado = modelos.EstadoEncuesta.finalizado
    bd.commit()
    bd.refresh(encuesta)
    return encuesta

# --- ENDPOINTS ---

