from typing import List, Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from app.database import obtener_bd
from app import modelos, schemas
from app.routers.auth import oauth2_scheme
from jose import JWTError, jwt
from app.security import CLAVE_SECRETA, ALGORITMO

router = APIRouter(
    prefix="/admin",
    tags=["Administración de Encuestas"]
)

# =============================================================================
# DEPENDENCIAS DE AUTENTICACIÓN Y AUTORIZACIÓN
# =============================================================================

def obtener_usuario_actual(
    token: Annotated[str, Depends(oauth2_scheme)],
    bd: Session = Depends(obtener_bd)
) -> modelos.UsuarioAdmin:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudieron validar las credenciales",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, CLAVE_SECRETA, algorithms=[ALGORITMO])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    # Buscar en BD para obtener id_admin y garantizar existencia
    usuario = bd.query(modelos.UsuarioAdmin).filter(
        modelos.UsuarioAdmin.nombre_usuario == username
    ).first()
    if usuario is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario no encontrado"
        )
    return usuario


def solo_administradores(
    usuario_actual: modelos.UsuarioAdmin = Depends(obtener_usuario_actual)
) -> modelos.UsuarioAdmin:
    if usuario_actual.rol != modelos.RolAdmin.ADMINISTRADOR:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos de administrador"
        )
    return usuario_actual


# =============================================================================
# FUNCIONES AUXILIARES
# =============================================================================

def crear_pregunta_con_opciones(bd: Session, id_encuesta: int, preg: schemas.PreguntaCrear):
    nueva_pregunta = modelos.Pregunta(
        id_encuesta=id_encuesta,
        texto_pregunta=preg.texto_pregunta,
        orden=preg.orden,
        tipo=preg.tipo,
        configuracion_json=preg.configuracion_json,
        activo=preg.activo
    )
    bd.add(nueva_pregunta)
    bd.flush()
    for opc in preg.opciones:
        nueva_opcion = modelos.OpcionRespuesta(
            id_pregunta=nueva_pregunta.id,
            texto_opcion=opc.texto_opcion,
            orden=opc.orden
        )
        bd.add(nueva_opcion)
    return nueva_pregunta


# =============================================================================
# ENDPOINTS
# =============================================================================

@router.post("/encuestas/", response_model=schemas.EncuestaSalida, status_code=status.HTTP_201_CREATED)
def crear_encuesta_completa(
    encuesta: schemas.EncuestaCrear,
    bd: Session = Depends(obtener_bd),
    usuario_actual: modelos.UsuarioAdmin = Depends(solo_administradores)
):
    acciones = [a.value for a in encuesta.acciones_disparadoras]
    
    nueva_encuesta = modelos.Encuesta(
        nombre=encuesta.nombre,
        descripcion=encuesta.descripcion,
        mensaje_final=encuesta.mensaje_final,
        fecha_inicio=encuesta.fecha_inicio,
        fecha_fin=encuesta.fecha_fin,
        prioridad=encuesta.prioridad,
        acciones_disparadoras=acciones,
        configuracion=encuesta.configuracion,
        estado=modelos.EstadoEncuesta.borrador,
        activo=encuesta.activo,
        # ✅ Campos de auditoría
        usuario_creacion=usuario_actual.id_admin
        # fecha_creacion se asigna por default en BD
    )
    
    bd.add(nueva_encuesta)
    bd.flush()  # Para obtener ID antes del commit

    # Crear reglas
    for regla in encuesta.reglas:
        nueva_regla = modelos.ReglaAsignacion(
            id_encuesta=nueva_encuesta.id,
            id_facultad=regla.id_facultad,
            id_carrera=regla.id_carrera,
            id_asignatura=regla.id_asignatura,
            publico_objetivo=regla.publico_objetivo
        )
        bd.add(nueva_regla)

    # Crear preguntas y opciones
    for preg in encuesta.preguntas:
        crear_pregunta_con_opciones(bd, nueva_encuesta.id, preg)

    bd.commit()
    # Recargar con relaciones para serialización completa
    encuesta_guardada = (
        bd.query(modelos.Encuesta)
        .options(
            joinedload(modelos.Encuesta.creador),
            joinedload(modelos.Encuesta.modificador),
            joinedload(modelos.Encuesta.reglas),
            joinedload(modelos.Encuesta.preguntas)
                .joinedload(modelos.Pregunta.opciones)
        )
        .filter(modelos.Encuesta.id == nueva_encuesta.id)
        .first()
    )
    return encuesta_guardada


@router.get("/encuestas/", response_model=List[schemas.EncuestaSalida])
def listar_encuestas(
    skip: int = 0,
    limit: int = 100,
    bd: Session = Depends(obtener_bd),
    usuario: modelos.UsuarioAdmin = Depends(obtener_usuario_actual)
):
    encuestas = (
        bd.query(modelos.Encuesta)
        .options(
            joinedload(modelos.Encuesta.creador),
            joinedload(modelos.Encuesta.modificador)
        )
        .offset(skip)
        .limit(limit)
        .all()
    )
    return encuestas


@router.get("/encuestas/{encuesta_id}", response_model=schemas.EncuestaSalida)
def obtener_encuesta(
    encuesta_id: int,
    bd: Session = Depends(obtener_bd),
    usuario: modelos.UsuarioAdmin = Depends(obtener_usuario_actual)
):
    encuesta = (
        bd.query(modelos.Encuesta)
        .options(
            joinedload(modelos.Encuesta.creador),
            joinedload(modelos.Encuesta.modificador),
            joinedload(modelos.Encuesta.reglas),
            joinedload(modelos.Encuesta.preguntas)
                .joinedload(modelos.Pregunta.opciones)
        )
        .filter(modelos.Encuesta.id == encuesta_id)
        .first()
    )
    if not encuesta:
        raise HTTPException(status_code=404, detail="Encuesta no encontrada")
    return encuesta


@router.put("/encuestas/{encuesta_id}", response_model=schemas.EncuestaSalida)
def actualizar_encuesta(
    encuesta_id: int,
    encuesta_actualizada: schemas.EncuestaCrear,
    bd: Session = Depends(obtener_bd),
    usuario_actual: modelos.UsuarioAdmin = Depends(solo_administradores)
):
    db_encuesta = bd.query(modelos.Encuesta).filter(modelos.Encuesta.id == encuesta_id).first()
    if not db_encuesta:
        raise HTTPException(status_code=404, detail="Encuesta no encontrada")

    # ✅ Registrar modificación
    db_encuesta.usuario_modificacion = usuario_actual.id_admin

    # Actualizar campos principales
    for campo, valor in encuesta_actualizada.model_dump(
        exclude={"reglas", "preguntas", "acciones_disparadoras"}
    ).items():
        setattr(db_encuesta, campo, valor)

    db_encuesta.acciones_disparadoras = [a.value for a in encuesta_actualizada.acciones_disparadoras]

    # Reemplazar reglas y preguntas (recreación completa)
    db_encuesta.reglas.clear()
    db_encuesta.preguntas.clear()
    bd.flush()

    for regla in encuesta_actualizada.reglas:
        nueva_regla = modelos.ReglaAsignacion(
            id_encuesta=encuesta_id,
            id_facultad=regla.id_facultad,
            id_carrera=regla.id_carrera,
            id_asignatura=regla.id_asignatura,
            publico_objetivo=regla.publico_objetivo
        )
        bd.add(nueva_regla)

    for preg in encuesta_actualizada.preguntas:
        crear_pregunta_con_opciones(bd, encuesta_id, preg)

    bd.commit()

    # Recargar con relaciones
    encuesta_actualizada_db = (
        bd.query(modelos.Encuesta)
        .options(
            joinedload(modelos.Encuesta.creador),
            joinedload(modelos.Encuesta.modificador),
            joinedload(modelos.Encuesta.reglas),
            joinedload(modelos.Encuesta.preguntas)
                .joinedload(modelos.Pregunta.opciones)
        )
        .filter(modelos.Encuesta.id == encuesta_id)
        .first()
    )
    return encuesta_actualizada_db


@router.post("/encuestas/{encuesta_id}/publicar", response_model=schemas.EncuestaSalida)
def publicar_encuesta(
    encuesta_id: int,
    bd: Session = Depends(obtener_bd),
    usuario: modelos.UsuarioAdmin = Depends(solo_administradores)
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
    # ✅ Registrar quién publicó (como modificación)
    encuesta.usuario_modificacion = usuario.id_admin
    
    bd.commit()
    bd.refresh(encuesta)
    return encuesta

@router.post("/encuestas/{encuesta_id}/duplicar", response_model=schemas.EncuestaSalida, status_code=status.HTTP_201_CREATED)
def duplicar_encuesta(
    encuesta_id: int,
    bd: Session = Depends(obtener_bd),
    usuario_actual: modelos.UsuarioAdmin = Depends(solo_administradores)
):
    """
    Duplica una encuesta existente, copiando todas sus configuraciones y preguntas.
    La nueva encuesta se crea en estado 'borrador'.
    """
    # 1. Obtener la encuesta original con todas sus relaciones
    encuesta_original = (
        bd.query(modelos.Encuesta)
        .options(
            joinedload(modelos.Encuesta.reglas),
            joinedload(modelos.Encuesta.preguntas)
                .joinedload(modelos.Pregunta.opciones)
        )
        .filter(modelos.Encuesta.id == encuesta_id)
        .first()
    )

    if not encuesta_original:
        raise HTTPException(status_code=404, detail="Encuesta no encontrada")

    # 2. Crear el clon de la encuesta
    nueva_encuesta = modelos.Encuesta(
        nombre=f"{encuesta_original.nombre} - (copia)",
        descripcion=encuesta_original.descripcion,
        mensaje_final=encuesta_original.mensaje_final,
        fecha_inicio=encuesta_original.fecha_inicio,
        fecha_fin=encuesta_original.fecha_fin,
        prioridad=encuesta_original.prioridad,
        acciones_disparadoras=list(encuesta_original.acciones_disparadoras), # Copia de lista
        configuracion=dict(encuesta_original.configuracion), # Copia de dict
        estado=modelos.EstadoEncuesta.borrador,
        activo=True, # Por defecto activa al duplicar
        usuario_creacion=usuario_actual.id_admin
    )

    bd.add(nueva_encuesta)
    bd.flush() # Obtener ID nuevo

    # 3. Clonar Reglas
    for regla in encuesta_original.reglas:
        nueva_regla = modelos.ReglaAsignacion(
            id_encuesta=nueva_encuesta.id,
            id_facultad=regla.id_facultad,
            id_carrera=regla.id_carrera,
            id_asignatura=regla.id_asignatura,
            publico_objetivo=regla.publico_objetivo
        )
        bd.add(nueva_regla)

    # 4. Clonar Preguntas y Opciones
    for preg in encuesta_original.preguntas:
        # Usamos el helper existente pero mapeando manualmente ya que no recibimos schema
        nueva_pregunta = modelos.Pregunta(
            id_encuesta=nueva_encuesta.id,
            texto_pregunta=preg.texto_pregunta,
            orden=preg.orden,
            tipo=preg.tipo,
            configuracion_json=dict(preg.configuracion_json) if preg.configuracion_json else None,
            activo=preg.activo
        )
        bd.add(nueva_pregunta)
        bd.flush()

        for opc in preg.opciones:
            nueva_opcion = modelos.OpcionRespuesta(
                id_pregunta=nueva_pregunta.id,
                texto_opcion=opc.texto_opcion,
                orden=opc.orden
            )
            bd.add(nueva_opcion)

    bd.commit()

    # 5. Retornar la nueva encuesta completa
    bd.refresh(nueva_encuesta)
    return nueva_encuesta

@router.delete("/encuestas/{encuesta_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_encuesta(
    encuesta_id: int,
    bd: Session = Depends(obtener_bd),
    usuario_actual: modelos.UsuarioAdmin = Depends(solo_administradores)
):
    """
    Elimina una encuesta. Solo permitido si está en estado 'borrador'.
    """
    encuesta = bd.query(modelos.Encuesta).filter(modelos.Encuesta.id == encuesta_id).first()

    if not encuesta:
        raise HTTPException(status_code=404, detail="Encuesta no encontrada")

    if encuesta.estado != modelos.EstadoEncuesta.borrador:
        raise HTTPException(
            status_code=400,
            detail="No se puede eliminar una encuesta que no esté en borrador (tiene histórico o está activa)."
        )

    bd.delete(encuesta)
    bd.commit()
    return None


@router.post("/encuestas/{encuesta_id}/finalizar", response_model=schemas.EncuestaSalida)
def finalizar_encuesta(
    encuesta_id: int,
    bd: Session = Depends(obtener_bd),
    usuario: modelos.UsuarioAdmin = Depends(solo_administradores)
):
    """
    Cambia el estado a FINALIZADO.
    """
    encuesta = bd.query(modelos.Encuesta).filter(modelos.Encuesta.id == encuesta_id).first()
    if not encuesta:
        raise HTTPException(status_code=404, detail="Encuesta no encontrada")
    
    if encuesta.estado == modelos.EstadoEncuesta.finalizado:
        raise HTTPException(status_code=400, detail="La encuesta ya está finalizada")

    encuesta.estado = modelos.EstadoEncuesta.finalizado
    # ✅ Registrar quién finalizó
    encuesta.usuario_modificacion = usuario.id_admin
    
    bd.commit()
    bd.refresh(encuesta)
    return encuesta