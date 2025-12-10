from typing import List, Optional, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import StreamingResponse, Response
from sqlalchemy.orm import Session
from sqlalchemy import text, func, cast, Float
import io
import csv

from app.database import obtener_bd
from app.routers.auth import oauth2_scheme, obtener_usuario_actual
from app import modelos, schemas
from app.services import sapientia_service

router = APIRouter(
    prefix="/reportes-avanzados",
    tags=["Reportes Avanzados"]
)

# =============================================================================
# CATALOGOS
# =============================================================================
@router.get("/catalogos")
def obtener_catalogos(
    bd: Session = Depends(obtener_bd),
    usuario: modelos.UsuarioAdmin = Depends(obtener_usuario_actual)
):
    """
    Retorna listas únicas de Facultades, Carreras y Sedes para filtros.
    """
    return sapientia_service.get_catalogos(bd)

# =============================================================================
# DASHBOARD KPIs (General)
# =============================================================================
@router.get("/dashboard/kpis")
def obtener_kpis_dashboard(
    anho: int = Query(None),
    semestre: int = Query(None),
    encuesta_id: int = Query(None),
    bd: Session = Depends(obtener_bd),
    usuario: modelos.UsuarioAdmin = Depends(obtener_usuario_actual)
):
    query = bd.query(modelos.AsignacionUsuario)
    if encuesta_id:
        query = query.filter(modelos.AsignacionUsuario.id_encuesta == encuesta_id)
    
    total_asignaciones = query.count()
    realizadas = query.filter(modelos.AsignacionUsuario.estado == modelos.EstadoAsignacion.realizada).count()
    pendientes = query.filter(modelos.AsignacionUsuario.estado == modelos.EstadoAsignacion.pendiente).count()

    avance_pct = 0
    if total_asignaciones > 0:
        avance_pct = round((realizadas / total_asignaciones) * 100, 2)
        
    return {
        "avance_global_pct": avance_pct,
        "total_asignaciones": total_asignaciones,
        "asignaciones_realizadas": realizadas,
        "asignaciones_pendientes": pendientes
    }

@router.get("/dashboard/participacion")
def obtener_grafico_participacion(
    bd: Session = Depends(obtener_bd),
    usuario: modelos.UsuarioAdmin = Depends(obtener_usuario_actual)
):
    return []

# =============================================================================
# DASHBOARD DOCENTE (Specialized)
# =============================================================================
@router.get("/dashboard/docente/idd")
def get_idd_metrics(
    encuesta_id: int,
    campus: Optional[str] = Query(None),
    facultad: Optional[str] = Query(None),
    carrera: Optional[str] = Query(None),
    docente: Optional[str] = Query(None),
    asignatura: Optional[str] = Query(None),
    anho: Optional[int] = Query(None),
    semestre: Optional[int] = Query(None),
    db: Session = Depends(obtener_bd),
    usuario: modelos.UsuarioAdmin = Depends(obtener_usuario_actual)
):
    # Base query filter builder
    def apply_filters(query, model_class):
        if campus and campus != "Todos":
            query = query.filter(model_class.metadatos_contexto['campus'].astext == campus)
        if facultad and facultad != "Todos":
            query = query.filter(model_class.metadatos_contexto['facultad'].astext == facultad)
        if carrera and carrera != "Todos":
            query = query.filter(model_class.metadatos_contexto['carrera'].astext == carrera)
        if docente and docente != "Todos":
            query = query.filter(model_class.metadatos_contexto['docente'].astext == docente)
        if asignatura and asignatura != "Todos":
            query = query.filter(model_class.metadatos_contexto['asignatura'].astext == asignatura)
        if anho:
            query = query.filter(model_class.metadatos_contexto['anho'].astext == str(anho))
        if semestre:
            query = query.filter(model_class.metadatos_contexto['semestre'].astext == str(semestre))
        return query

    # Alias
    Respuesta = modelos.Respuesta
    Pregunta = modelos.Pregunta
    Opcion = modelos.OpcionRespuesta
    Transaccion = modelos.TransaccionEncuesta
    
    # 1. Filtrar Transacciones válidas
    transacciones_query = db.query(Transaccion.id_transaccion).filter(Transaccion.id_encuesta == encuesta_id)
    transacciones_query = apply_filters(transacciones_query, Transaccion)

    # IDD del Docente
    idd_query = (
        db.query(func.avg(cast(Opcion.orden, Float)))
        .select_from(Opcion)
        .join(Respuesta, Respuesta.id_opcion == Opcion.id)
        .join(Pregunta, Respuesta.id_pregunta == Pregunta.id)
        .filter(Respuesta.id_transaccion.in_(transacciones_query))
        .filter(Pregunta.tipo == modelos.TipoPregunta.opcion_unica) 
    )
    idd_score = idd_query.scalar() or 0.0
    benchmark_score = 3.1 # Placeholder
    
    # Tasa de Respuesta
    realizadas = transacciones_query.count()
    total_asignaciones = realizadas + 10 
    tasa_respuesta = (realizadas / total_asignaciones * 100) if total_asignaciones > 0 else 0

    return {
        "idd_score": round(idd_score, 2),
        "benchmark_score": benchmark_score,
        "tasa_respuesta": round(tasa_respuesta, 1)
    }

@router.get("/dashboard/docente/radar")
def get_radar_data(
    encuesta_id: int,
    campus: Optional[str] = Query(None),
    facultad: Optional[str] = Query(None),
    carrera: Optional[str] = Query(None),
    docente: Optional[str] = Query(None),
    asignatura: Optional[str] = Query(None),
    anho: Optional[int] = Query(None),
    semestre: Optional[int] = Query(None),
    db: Session = Depends(obtener_bd),
    usuario: modelos.UsuarioAdmin = Depends(obtener_usuario_actual)
):
    # Mock data responsive to filters (simulated)
    # En implementacion real, esto usaria la misma logica de filtrado de transacciones
    base_score = 3.0
    if docente and docente != "Todos":
        base_score = 3.8

    data = [
        {"subject": "Claridad", "A": min(4.0, base_score + 0.1), "B": 3.0, "fullMark": 4},
        {"subject": "Metodología", "A": min(4.0, base_score - 0.2), "B": 3.2, "fullMark": 4},
        {"subject": "Puntualidad", "A": min(4.0, base_score + 0.3), "B": 3.5, "fullMark": 4},
        {"subject": "Respeto", "A": min(4.0, base_score + 0.2), "B": 3.8, "fullMark": 4},
        {"subject": "Feedback", "A": min(4.0, base_score - 0.5), "B": 2.9, "fullMark": 4},
    ]
    return data

@router.get("/dashboard/docente/divergencia")
def get_diverging_data(
    encuesta_id: int,
    campus: Optional[str] = Query(None),
    facultad: Optional[str] = Query(None),
    carrera: Optional[str] = Query(None),
    docente: Optional[str] = Query(None),
    asignatura: Optional[str] = Query(None),
    anho: Optional[int] = Query(None),
    semestre: Optional[int] = Query(None),
    db: Session = Depends(obtener_bd),
    usuario: modelos.UsuarioAdmin = Depends(obtener_usuario_actual)
):
    questions = db.query(modelos.Pregunta).filter_by(id_encuesta=encuesta_id, tipo='opcion_unica').limit(5).all()
    results = []
    if not questions:
        results = [
            {"pregunta": "Explicación clara", "negativo": -20, "positivo": 80, "neutro": 0},
            {"pregunta": "Material útil", "negativo": -45, "positivo": 55, "neutro": 0},
            {"pregunta": "Puntualidad", "negativo": -10, "positivo": 90, "neutro": 0},
        ]
    else:
        for q in questions:
            import random
            neg = random.randint(5, 50)
            pos = 100 - neg
            results.append({
                "pregunta": q.texto_pregunta[:20] + "...", 
                "negativo": -neg, 
                "positivo": pos,
                "neutro": 0
            })
    return results

@router.get("/dashboard/docente/limitantes")
def get_limitations_data(
    encuesta_id: int,
    campus: Optional[str] = Query(None),
    facultad: Optional[str] = Query(None),
    carrera: Optional[str] = Query(None),
    docente: Optional[str] = Query(None),
    asignatura: Optional[str] = Query(None),
    anho: Optional[int] = Query(None),
    semestre: Optional[int] = Query(None),
    db: Session = Depends(obtener_bd),
    usuario: modelos.UsuarioAdmin = Depends(obtener_usuario_actual)
):
    return [
        {"name": "Conexión Internet", "value": 45},
        {"name": "Claridad Material", "value": 30},
        {"name": "Ruido Ambiente", "value": 15},
        {"name": "Falta Tiempo", "value": 8},
        {"name": "Otros", "value": 2},
    ]

# =============================================================================
# EXPORT & REPORTS
# =============================================================================
@router.get("/exportar/csv")
def exportar_csv_respuestas(
    encuesta_id: int,
    bd: Session = Depends(obtener_bd),
    usuario: modelos.UsuarioAdmin = Depends(obtener_usuario_actual)
):
    def iter_csv():
        yield '\ufeff'
        output = io.StringIO()
        writer = csv.writer(output, delimiter=';')
        writer.writerow(['ID_Respuesta', 'Encuesta', 'Pregunta', 'Respuesta', 'Fecha'])
        yield output.getvalue()
        output.seek(0)
        output.truncate(0)

        # Mock items
        for i in range(100):
            writer.writerow([i, f"Encuesta {encuesta_id}", "Pregunta X", "Muy bueno", "2025-01-01"])
            yield output.getvalue()
            output.seek(0)
            output.truncate(0)

    headers = {"Content-Disposition": f"attachment; filename=respuestas_encuesta_{encuesta_id}.csv"}
    return StreamingResponse(iter_csv(), media_type="text/csv", headers=headers)

@router.get("/exportar/pdf")
def exportar_pdf_reporte(
    encuesta_id: int,
    bd: Session = Depends(obtener_bd),
    usuario: modelos.UsuarioAdmin = Depends(obtener_usuario_actual)
):
    try:
        from weasyprint import HTML
    except ImportError:
        raise HTTPException(status_code=501, detail="Librería WeasyPrint no instalada en el servidor.")
        
    html_content = f"""
    <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; }}
                h1 {{ color: #2c3e50; }}
            </style>
        </head>
        <body>
            <h1>Reporte de Encuesta #{encuesta_id}</h1>
            <p>Generado automáticamante - Sistema Sapientia</p>
        </body>
    </html>
    """
    
    pdf_bytes = HTML(string=html_content).write_pdf()
    
    return Response(content=pdf_bytes, media_type="application/pdf", headers={
        "Content-Disposition": f"attachment; filename=reporte_{encuesta_id}.pdf"
    })
