from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.database import obtener_bd
from app.routers.auth import obtener_usuario_actual
from app import modelos as mod
from app import schemas as sch

router = APIRouter(
    prefix="/sapientia",
    tags=["Integración Sapientia"],
    dependencies=[Depends(obtener_usuario_actual)]
)

# =============================================================================
# LOGICA DE NEGOCIO (HELPERS)
# =============================================================================

def _get_campus(bd: Session) -> List[str]:
    rows = bd.execute(text("SELECT DISTINCT campus FROM sapientia.oferta_academica ORDER BY campus")).fetchall()
    return [r[0] for r in rows if r[0]]

def _get_facultades(bd: Session, campus: Optional[str] = None) -> List[str]:
    sql = "SELECT DISTINCT facultad FROM sapientia.oferta_academica WHERE 1=1"
    params = {}
    if campus:
        sql += " AND campus = :campus"
        params["campus"] = campus
    sql += " ORDER BY facultad"
    
    rows = bd.execute(text(sql), params).fetchall()
    return [r[0] for r in rows if r[0]]

def _get_departamentos(bd: Session, campus: Optional[str] = None, facultad: Optional[str] = None) -> List[str]:
    sql = "SELECT DISTINCT departamento FROM sapientia.oferta_academica WHERE 1=1"
    params = {}
    if campus:
        sql += " AND campus = :campus"
        params["campus"] = campus
    if facultad:
        sql += " AND facultad = :facultad"
        params["facultad"] = facultad
    sql += " ORDER BY departamento"
    
    rows = bd.execute(text(sql), params).fetchall()
    return [r[0] for r in rows if r[0]]

def _get_asignaturas(bd: Session, campus: Optional[str] = None, facultad: Optional[str] = None, departamento: Optional[str] = None, docente: Optional[str] = None) -> List[Dict[str, Any]]:
    sql = """
        SELECT DISTINCT cod_asignatura, asignatura, seccion 
        FROM sapientia.oferta_academica 
        WHERE 1=1
    """
    params = {}
    if campus:
        sql += " AND campus = :campus"
        params["campus"] = campus
    if facultad:
        sql += " AND facultad = :facultad"
        params["facultad"] = facultad
    if departamento:
        sql += " AND departamento = :departamento"
        params["departamento"] = departamento
    if docente:
        sql += " AND docente = :docente"
        params["docente"] = docente
        
    sql += " ORDER BY asignatura, seccion"
    
    rows = bd.execute(text(sql), params).fetchall()
    return [
        {"codigo": r[0], "nombre": r[1], "seccion": r[2]} 
        for r in rows
    ]

def _get_docentes(bd: Session, campus: Optional[str] = None, facultad: Optional[str] = None, departamento: Optional[str] = None) -> List[str]:
    sql = "SELECT DISTINCT docente FROM sapientia.oferta_academica WHERE docente IS NOT NULL"
    params = {}
    if campus:
        sql += " AND campus = :campus"
        params["campus"] = campus
    if facultad:
        sql += " AND facultad = :facultad"
        params["facultad"] = facultad
    if departamento:
        sql += " AND departamento = :departamento"
        params["departamento"] = departamento
        
    sql += " ORDER BY docente"
    
    rows = bd.execute(text(sql), params).fetchall()
    return [r[0] for r in rows if r[0]]

# =============================================================================
# ENDPOINTS ESPECIFICOS
# =============================================================================

@router.get("/campus", response_model=List[str])
def get_campus(bd: Session = Depends(obtener_bd)):
    """Retorna lista de Campus distintos"""
    return _get_campus(bd)

@router.get("/facultades", response_model=List[str])
def get_facultades(
    campus: Optional[str] = Query(None),
    bd: Session = Depends(obtener_bd)
):
    return _get_facultades(bd, campus)

@router.get("/departamentos", response_model=List[str])
def get_departamentos(
    campus: Optional[str] = Query(None),
    facultad: Optional[str] = Query(None),
    bd: Session = Depends(obtener_bd)
):
    return _get_departamentos(bd, campus, facultad)

@router.get("/asignaturas", response_model=List[dict])
def get_asignaturas(
    campus: Optional[str] = Query(None),
    facultad: Optional[str] = Query(None),
    departamento: Optional[str] = Query(None),
    docente: Optional[str] = Query(None),
    bd: Session = Depends(obtener_bd)
):
    return _get_asignaturas(bd, campus, facultad, departamento, docente)

@router.get("/docentes", response_model=List[str])
def get_docentes(
    campus: Optional[str] = Query(None),
    facultad: Optional[str] = Query(None),
    departamento: Optional[str] = Query(None),
    bd: Session = Depends(obtener_bd)
):
    return _get_docentes(bd, campus, facultad, departamento)

@router.get("/alumnos", response_model=List[dict])
def get_alumnos_contexto(
    cod_asignatura: str = Query(...),
    seccion: str = Query(...),
    bd: Session = Depends(obtener_bd)
):
    """
    Retorna alumnos inscritos en una asignatura/sección específica.
    """
    sql = """
        SELECT i.id_alumno 
        FROM sapientia.inscripciones i
        WHERE i.cod_asignatura = :cod AND i.seccion = :sec
    """
    rows = bd.execute(text(sql), {"cod": cod_asignatura, "sec": seccion}).fetchall()
    
    # Sintetizamos nombre ya que no tenemos tabla alumnos real
    return [
        {"id": r[0], "nombre": f"Alumno {r[0]}"}
        for r in rows
    ]

# =============================================================================
# ENDPOINT GENERICO (Compatibilidad Frontend)
# =============================================================================

@router.get("/catalogos/{tipo}", response_model=List[str])
def get_catalogo_generico(
    tipo: str,
    bd: Session = Depends(obtener_bd)
):
    """
    Endpoint genérico usado por componentes legacy del Frontend (ej. ConstructorReglas).
    Mapea el 'tipo' a la consulta específica correspondiente.
    """
    tipo = tipo.lower()

    if tipo == "campus":
        return _get_campus(bd)
    
    elif tipo == "facultad":
        return _get_facultades(bd)
    
    elif tipo in ["departamento", "carrera"]:
        return _get_departamentos(bd)
    
    elif tipo == "docente":
        return _get_docentes(bd)
    
    elif tipo == "asignatura":
        # Para asignaturas strings, formateamos: "Nombre (Codigo)"
        # Reusamos la logica de get_asignaturas pero formateamos
        raw_asig = _get_asignaturas(bd) # Retorna dicts
        # Evitar duplicados de nombre si hay multiples secciones
        # Pero ConstructorReglas espera string. Uniquificamos por string resultante.
        nombres = {f"{a['nombre']} ({a['codigo']})" for a in raw_asig}
        return sorted(list(nombres))

    else:
        return []

# =============================================================================
# ENDPOINTS DE INTEGRACIÓN (CU11 / CU07)
# =============================================================================

@router.post("/verificar-estado", response_model=sch.RespuestaVerificacionEstado)
def verificar_estado_alumno(
    id_alumno: int,
    bd: Session = Depends(obtener_bd)
):
    """
    CU11: Sapientia consulta si el alumno tiene encuestas pendientes obligatorias/bloqueantes.
    """
    asignacion = bd.query(mod.AsignacionUsuario).join(mod.Encuesta).filter(
        mod.AsignacionUsuario.id_usuario == id_alumno,
        mod.AsignacionUsuario.estado == mod.EstadoAsignacion.pendiente,
        mod.Encuesta.activo == True,
        mod.Encuesta.estado == mod.EstadoEncuesta.en_curso,
        mod.Encuesta.prioridad == mod.PrioridadEncuesta.obligatoria
    ).first()

    if asignacion:
        return {
            "estado_bloqueo": True,
            "mensaje": f"Tienes una encuesta pendiente: {asignacion.encuesta.nombre}",
            "id_encuesta_pendiente": asignacion.id_encuesta,
            "datos_encuesta": None 
        }
    
    return {
        "estado_bloqueo": False,
        "mensaje": "Habilitado",
        "id_encuesta_pendiente": None
    }

@router.post("/recepcionar-respuestas", status_code=200)
def recibir_respuestas(
    envio: sch.EnvioRespuestasAlumno,
    bd: Session = Depends(obtener_bd)
):
    """
    CU07: Recibe las respuestas desde Sapientia (o Frontend simulado).
    """
    # 1. Verificar Asignación
    asignacion = bd.query(mod.AsignacionUsuario).filter(
        mod.AsignacionUsuario.id_usuario == envio.id_usuario,
        mod.AsignacionUsuario.id_encuesta == envio.id_encuesta,
    ).first()

    if not asignacion:
        pass

    # QA Fix: Validación de Integridad de Datos.
    ids_preguntas_enviadas = {r.id_pregunta for r in envio.respuestas}
    if ids_preguntas_enviadas:
        preguntas_validas = bd.query(mod.Pregunta.id).filter(
            mod.Pregunta.id_encuesta == envio.id_encuesta,
            mod.Pregunta.id.in_(ids_preguntas_enviadas)
        ).all()
        ids_validos = {p[0] for p in preguntas_validas}
        
        if len(ids_validos) != len(ids_preguntas_enviadas):
             invalidas = ids_preguntas_enviadas - ids_validos
             raise HTTPException(
                 status_code=400, 
                 detail=f"Integridad de datos fallida: Las preguntas {invalidas} no pertenecen a la encuesta {envio.id_encuesta}"
             )

    # 2. Registrar Transacción
    import hashlib
    salt = "SAPIENTIA_SECRET_SALT_2025" 
    hash_usuario = hashlib.sha256(f"{envio.id_usuario}{salt}".encode()).hexdigest()

    # --- DATOS DE CONTEXTO ---
    # Recuperamos metadatos de la asignación si existen
    meta_asignacion = asignacion.metadatos_asignacion if (asignacion and asignacion.metadatos_asignacion) else {}
    
    # Contexto base del envío (app móvil/frontend)
    contexto_final = {
        "origen": "sapientia_api", 
        "hash_usuario": hash_usuario, 
        "id_referencia": envio.id_referencia_contexto,
        **envio.metadatos_contexto
    }

    # Merge: Metadatos de asignación tienen precedencia o complementan
    # IMPORTANTE: Mapeo de claves para ETL (etl.py espera 'profesor', 'asignatura')
    # sapientia_service.py genera 'docente', 'materia'
    
    if "docente" in meta_asignacion:
        contexto_final["profesor"] = meta_asignacion["docente"]
    
    if "materia" in meta_asignacion:
        contexto_final["asignatura"] = meta_asignacion["materia"]
        
    # Copiamos el resto de metadatos útiles
    for k, v in meta_asignacion.items():
        if k not in contexto_final:
            contexto_final[k] = v

    new_trans = mod.TransaccionEncuesta(
        id_encuesta=envio.id_encuesta,
        metadatos_contexto=contexto_final,
        procesado_etl=False
    )
    bd.add(new_trans)
    bd.flush()
    
    nueva_transaccion = new_trans # Mantener nombre variable para codigo siguiente

    # 3. Guardar Respuestas
    for r in envio.respuestas:
        nueva_resp = mod.Respuesta(
            id_transaccion=nueva_transaccion.id_transaccion,
            id_pregunta=r.id_pregunta,
            valor_respuesta=r.valor_respuesta,
            id_opcion=r.id_opcion
        )
        bd.add(nueva_resp)

    # 4. Actualizar Asignación
    if asignacion:
        asignacion.estado = mod.EstadoAsignacion.realizada
        asignacion.fecha_realizacion = text("now()")
    
    bd.commit()
    return {"mensaje": "Respuestas recibidas correctamente"}

# =============================================================================
# ENDPOINTS PARA BORRADOR (RF08 - Guardar Progreso Parcial)
# =============================================================================

@router.post("/guardar-borrador", status_code=200)
def guardar_borrador(
    request: sch.GuardarBorradorRequest,
    bd: Session = Depends(obtener_bd)
):
    """
    RF08: Guarda el progreso parcial de una encuesta como borrador.
    El usuario puede continuar más tarde sin perder su trabajo.
    """
    # 1. Verificar que la asignación existe
    asignacion = bd.query(mod.AsignacionUsuario).filter(
        mod.AsignacionUsuario.id == request.id_asignacion
    ).first()
    
    if not asignacion:
        raise HTTPException(status_code=404, detail="Asignación no encontrada")
    
    # 2. Buscar o crear registro de borrador
    borrador = bd.query(mod.RespuestaBorrador).filter(
        mod.RespuestaBorrador.id_asignacion == request.id_asignacion
    ).first()
    
    # Convertir respuestas a formato JSON serializable
    respuestas_json = [
        {
            "id_pregunta": r.id_pregunta,
            "valor_respuesta": r.valor_respuesta,
            "id_opcion": r.id_opcion
        }
        for r in request.respuestas
    ]
    
    if borrador:
        # Actualizar borrador existente
        borrador.respuestas_json = respuestas_json
        # fecha_actualizacion se actualiza automáticamente con onupdate=func.now()
    else:
        # Crear nuevo borrador
        borrador = mod.RespuestaBorrador(
            id_asignacion=request.id_asignacion,
            respuestas_json=respuestas_json
        )
        bd.add(borrador)
    
    bd.commit()
    bd.refresh(borrador)
    
    return {
        "mensaje": "Borrador guardado exitosamente",
        "id_asignacion": request.id_asignacion,
        "fecha_actualizacion": borrador.fecha_actualizacion
    }

@router.get("/borrador/{id_asignacion}", response_model=sch.BorradorResponse)
def obtener_borrador(
    id_asignacion: int,
    bd: Session = Depends(obtener_bd)
):
    """
    RF08: Recupera un borrador guardado previamente para continuar la encuesta.
    """
    borrador = bd.query(mod.RespuestaBorrador).filter(
        mod.RespuestaBorrador.id_asignacion == id_asignacion
    ).first()
    
    if not borrador:
        raise HTTPException(status_code=404, detail="No hay borrador guardado para esta asignación")
    
    # Convertir JSON a objetos Pydantic
    respuestas = [
        sch.RespuestaIndividual(
            id_pregunta=r["id_pregunta"],
            valor_respuesta=r.get("valor_respuesta"),
            id_opcion=r.get("id_opcion")
        )
        for r in borrador.respuestas_json
    ]
    
    return sch.BorradorResponse(
        id_asignacion=id_asignacion,
        respuestas=respuestas,
        fecha_actualizacion=borrador.fecha_actualizacion
    )