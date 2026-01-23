from typing import List, Annotated, Optional
import logging
import os
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload
from app.database import obtener_bd
from app import modelos, schemas
from app.routers.auth import oauth2_scheme
from jose import JWTError, jwt
from app.security import CLAVE_SECRETA, ALGORITMO
from app.services import sapientia_service
# Importar nuevo servicio de dominio
from app.servicios.encuesta_servicio import EncuestaServicio
from datetime import datetime, timezone

# Configurar logger
logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/admin",
    tags=["Administración de Encuestas"]
)

# Configuración desde variables de entorno
BATCH_SIZE_JIT = int(os.getenv("BATCH_SIZE_JIT", "1000"))
BATCH_SIZE_PUBLICACION = int(os.getenv("BATCH_SIZE_PUBLICACION", "1000"))

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
            publico_objetivo=regla.publico_objetivo,
            filtros_json=regla.filtros_json
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


@router.get("/encuestas/", response_model=List[schemas.EncuestaResumen])
def listar_encuestas(
    skip: int = 0,
    limit: int = 100,
    term: Optional[str] = None, # Parámetro de búsqueda
    estados: Annotated[Optional[List[modelos.EstadoEncuesta]], Query()] = None, # Nuevo filtro de estados
    bd: Session = Depends(obtener_bd),
    usuario: modelos.UsuarioAdmin = Depends(obtener_usuario_actual)
):
    query = bd.query(modelos.Encuesta)

    if term:
        # Filtro ilike para búsqueda insensible a mayúsculas
        query = query.filter(modelos.Encuesta.nombre.ilike(f"%{term}%"))
    
    if estados:
        query = query.filter(modelos.Encuesta.estado.in_(estados))

    encuestas = (
        query
        .options(
            joinedload(modelos.Encuesta.creador),
            joinedload(modelos.Encuesta.modificador),
            # Pre-cargar relaciones ligeras esenciales para propiedades calculadas si fuera necesario, 
            # pero para cantidad_preguntas/respuestas, si son properties en Python, aun requieren carga o subquery.
            # OPTIMIZACION: Para evitar cargar millones de preguntas, idealmente se usaría group_by o column_property.
            # Por ahora, al NO acceder a .preguntas en el schema Resumen, SQLAlchemy NO debería disparar el lazy load 
            # a menos que 'cantidad_preguntas' acceda a self.preguntas.
            joinedload(modelos.Encuesta.preguntas), 
            joinedload(modelos.Encuesta.asignaciones)
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
    print(f"DEBUG: Entering actualizar_encuesta with ID {encuesta_id}")
    print(f"DEBUG: Payload: {encuesta_actualizada.model_dump(exclude={'reglas', 'preguntas', 'acciones_disparadoras'})}")
    print(f"DEBUG: Reglas Payload: {encuesta_actualizada.reglas}")
    logger.debug(f"Starting update for encuesta {encuesta_id} with row lock")
    db_encuesta = (
        bd.query(modelos.Encuesta)
        # .with_for_update()  <-- REMOVIDO: Causa error 500 en SQLite (syntax error near FOR UPDATE)
        .options(joinedload(modelos.Encuesta.preguntas))
        .filter(modelos.Encuesta.id == encuesta_id)
        .first()
    )
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
    # Reemplazar reglas y preguntas (recreación completa)
    # Usamos delete() explícito para asegurar limpieza total y evitar problemas con el ORM session cache
    bd.query(modelos.ReglaAsignacion).filter(modelos.ReglaAsignacion.id_encuesta == encuesta_id).delete()
    bd.query(modelos.OpcionRespuesta).filter(modelos.OpcionRespuesta.pregunta.has(id_encuesta=encuesta_id)).delete(synchronize_session=False) # Borrar opciones de las preguntas
    bd.query(modelos.Pregunta).filter(modelos.Pregunta.id_encuesta == encuesta_id).delete()
    
    bd.flush()

    for regla in encuesta_actualizada.reglas:
        nueva_regla = modelos.ReglaAsignacion(
            id_encuesta=encuesta_id,
            id_facultad=regla.id_facultad,
            id_carrera=regla.id_carrera,
            id_asignatura=regla.id_asignatura,
            publico_objetivo=regla.publico_objetivo,
            filtros_json=regla.filtros_json
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
    Cambia el estado de BORRADOR a EN_CURSO y genera asignaciones JIT si corresponde.
    """
    """
    Cambia el estado de BORRADOR a EN_CURSO y genera asignaciones JIT si corresponde.
    """
    # Delegamos lógica de negocio compleja al servicio de dominio (SOLID)
    return EncuestaServicio.publicar_encuesta(
        db=bd,
        encuesta_id=encuesta_id,
        usuario_id=usuario.id_admin,
        batch_size_jit=BATCH_SIZE_JIT,
        batch_size_pub=BATCH_SIZE_PUBLICACION
    )

def crear_asignacion_si_no_existe(bd: Session, id_encuesta: int, id_usuario: int, id_contexto: str, metadatos: dict):
    existe = bd.query(modelos.AsignacionUsuario).filter(
        modelos.AsignacionUsuario.id_usuario == id_usuario,
        modelos.AsignacionUsuario.id_encuesta == id_encuesta,
        modelos.AsignacionUsuario.id_referencia_contexto == id_contexto
    ).first()

    if not existe:
        nueva = modelos.AsignacionUsuario(
            id_usuario=id_usuario,
            id_encuesta=id_encuesta,
            id_referencia_contexto=id_contexto,
            metadatos_asignacion=metadatos,
            estado=modelos.EstadoAsignacion.pendiente
        )
        bd.add(nueva)




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

    return EncuestaServicio.duplicar_encuesta(
        db=bd,
        encuesta_id=encuesta_id,
        usuario_id=usuario_actual.id_admin
    )

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