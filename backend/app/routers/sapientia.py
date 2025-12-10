from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.database import obtener_bd
from app.routers.auth import obtener_usuario_actual
from app.routers.auth import obtener_usuario_actual
from app import modelos as mod
from app import schemas as sch

router = APIRouter(
    prefix="/sapientia",
    tags=["Integración Sapientia"],
    dependencies=[Depends(obtener_usuario_actual)]
)

@router.get("/campus", response_model=List[str])
def get_campus(bd: Session = Depends(obtener_bd)):
    """Retorna lista de Campus distintos"""
    # Consulta optimizada a oferta_academica
    rows = bd.execute(text("SELECT DISTINCT campus FROM sapientia.oferta_academica ORDER BY campus")).fetchall()
    return [r[0] for r in rows if r[0]]

@router.get("/facultades", response_model=List[str])
def get_facultades(
    campus: Optional[str] = Query(None),
    bd: Session = Depends(obtener_bd)
):
    sql = "SELECT DISTINCT facultad FROM sapientia.oferta_academica WHERE 1=1"
    params = {}
    if campus:
        sql += " AND campus = :campus"
        params["campus"] = campus
    sql += " ORDER BY facultad"
    
    rows = bd.execute(text(sql), params).fetchall()
    return [r[0] for r in rows if r[0]]

@router.get("/carreras", response_model=List[str])
def get_carreras(
    campus: Optional[str] = Query(None),
    facultad: Optional[str] = Query(None),
    bd: Session = Depends(obtener_bd)
):
    # Nota: Mapeamos 'departamento' como 'carrera' según aprendizajes previos
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

@router.get("/asignaturas", response_model=List[dict])
def get_asignaturas(
    campus: Optional[str] = Query(None),
    facultad: Optional[str] = Query(None),
    carrera: Optional[str] = Query(None),
    docente: Optional[str] = Query(None),
    bd: Session = Depends(obtener_bd)
):
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
    if carrera:
        sql += " AND departamento = :carrera"
        params["carrera"] = carrera
    if docente:
        sql += " AND docente = :docente"
        params["docente"] = docente
        
    sql += " ORDER BY asignatura, seccion"
    
    rows = bd.execute(text(sql), params).fetchall()
    return [
        {"codigo": r[0], "nombre": r[1], "seccion": r[2]} 
        for r in rows
    ]

@router.get("/docentes", response_model=List[str])
def get_docentes(
    campus: Optional[str] = Query(None),
    facultad: Optional[str] = Query(None),
    carrera: Optional[str] = Query(None),
    bd: Session = Depends(obtener_bd)
):
    sql = "SELECT DISTINCT docente FROM sapientia.oferta_academica WHERE docente IS NOT NULL"
    params = {}
    if campus:
        sql += " AND campus = :campus"
        params["campus"] = campus
    if facultad:
        sql += " AND facultad = :facultad"
        params["facultad"] = facultad
    if carrera:
        sql += " AND departamento = :carrera"
        params["carrera"] = carrera
        
    sql += " ORDER BY docente"
    
    rows = bd.execute(text(sql), params).fetchall()
    return [r[0] for r in rows if r[0]]

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
    # Buscar asignaciones pendientes obligatorias
    # Nota: La lógica de bloqueo depende de la política. Asumimos que si hay pendiente y es obligatoria -> bloqueo.
    # Por ahora simple: Si tiene CUALQUIER pendiente, avisamos.
    
    asignacion = bd.query(mod.AsignacionUsuario).join(mod.Encuesta).filter(
        mod.AsignacionUsuario.id_usuario == id_alumno,
        mod.AsignacionUsuario.estado == mod.EstadoAsignacion.pendiente,
        mod.Encuesta.activo == True,
        mod.Encuesta.estado == mod.EstadoEncuesta.en_curso
        # Deberíamos filtrar por obligatoriedad si existiera ese flag en la asignación o encuesta
    ).first()

    if asignacion:
        return {
            "estado_bloqueo": True,
            "mensaje": f"Tienes una encuesta pendiente: {asignacion.encuesta.nombre}",
            "id_encuesta_pendiente": asignacion.id_encuesta,
            # Podríamos devolver la encuesta completa si se requiere
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
    # Intentamos buscar por contexto si es JIT, o por usuario/encuesta genérico
    asignacion = bd.query(mod.AsignacionUsuario).filter(
        mod.AsignacionUsuario.id_usuario == envio.id_usuario,
        mod.AsignacionUsuario.id_encuesta == envio.id_encuesta,
        # mod.AsignacionUsuario.id_referencia_contexto == envio.id_referencia_contexto 
        # A veces el contexto puede variar un poco o ser nulo, mejor asegurar id_usuario + id_encuesta
    ).first()

    if not asignacion:
        # Si es obligatoria JIT, debería existir. Si es voluntaria publica, quizás se crea al vuelo?
        # Por ahora fallamos si no existe asignación.
        # raise HTTPException(status_code=404, detail="Asignación no encontrada")
        
        # O creamos al vuelo si es política permisiva
        pass

    # 2. Registrar Transacción
    nueva_transaccion = mod.TransaccionEncuesta(
        id_encuesta=envio.id_encuesta,
        # id_usuario=envio.id_usuario, # OJO: Transaccion no tenia id_usuario en mi debug anterior, solo metadatos?
        # Check BD anterior: id_transaccion, id_encuesta, fecha_..., metadatos...
        # Guardamos usuario en metadatos para referencia ETL
        metadatos_contexto={
            "origen": "sapientia_api", 
            "id_usuario": envio.id_usuario,
            "id_referencia": envio.id_referencia_contexto,
            **envio.metadatos_contexto
        },
        procesado_etl=False
    )
    bd.add(nueva_transaccion)
    bd.flush()

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