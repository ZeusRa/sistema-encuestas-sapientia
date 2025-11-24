from typing import List, Dict, Any
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text, func
from app.database import obtener_bd
from app import modelos, schemas
from app.routers.admin import obtener_usuario_actual 
router = APIRouter(
    prefix="/reportes",
    tags=["Reportes y Analítica (OLAP)"]
)

@router.get("/stats-generales", response_model=schemas.DashboardStats)
def obtener_estadisticas_generales(
    bd: Session = Depends(obtener_bd),
    usuario: dict = Depends(obtener_usuario_actual)
):
    """
    Devuelve contadores rápidos para las tarjetas del Dashboard.
    """
    # Consultamos directamente la tabla de hechos OLAP
    total_hechos = bd.query(func.count(modelos.HechosRespuestas.id_hecho)).scalar()
    
    # Consultamos OLTP para saber cuántas transacciones hay en total
    total_transacciones = bd.query(func.count(modelos.TransaccionEncuesta.id_transaccion)).scalar()
    
    # Simulamos la fecha de última actualización (podría venir de una tabla de logs ETL)
    import datetime
    ultima_act = datetime.datetime.now() 

    return {
        "total_encuestas_completadas": total_transacciones,
        "total_respuestas_procesadas": total_hechos,
        "ultime_actualizacion_etl": ultima_act
    }

@router.get("/participacion-por-facultad", response_model=List[schemas.ReporteParticipacion])
def reporte_participacion_facultad(
    bd: Session = Depends(obtener_bd),
    usuario: dict = Depends(obtener_usuario_actual)
):
    """
    Agrupa la cantidad de respuestas recibidas por Facultad.
    Usa el esquema OLAP (DimUbicacion + Hechos).
    """
    query = text("""
        SELECT 
            u.nombre_facultad as facultad,
            COUNT(DISTINCT h.id_transaccion_origen) as cantidad_respuestas
        FROM encuestas_olap.hechos_respuestas h
        JOIN encuestas_olap.dim_ubicacion u ON h.id_dim_ubicacion = u.id_dim_ubicacion
        GROUP BY u.nombre_facultad
        ORDER BY cantidad_respuestas DESC
    """)
    
    resultados = bd.execute(query).fetchall()
    
    # Convertir a lista de diccionarios/esquemas
    return [
        {"facultad": row.facultad, "cantidad_respuestas": row.cantidad_respuestas}
        for row in resultados
    ]

@router.get("/promedios-por-pregunta", response_model=List[schemas.ReportePromedioPregunta])
def reporte_promedios(
    bd: Session = Depends(obtener_bd),
    usuario: dict = Depends(obtener_usuario_actual)
):
    """
    Calcula el promedio numérico de las respuestas para cada pregunta.
    Solo considera respuestas que pudieron convertirse a número.
    """
    query = text("""
        SELECT 
            p.texto_pregunta as pregunta,
            AVG(h.respuesta_numerica) as promedio,
            COUNT(h.id_hecho) as total_respuestas
        FROM encuestas_olap.hechos_respuestas h
        JOIN encuestas_olap.dim_pregunta p ON h.id_dim_pregunta = p.id_dim_pregunta
        WHERE h.respuesta_numerica IS NOT NULL
        GROUP BY p.texto_pregunta
        ORDER BY promedio DESC
    """)
    
    resultados = bd.execute(query).fetchall()
    
    return [
        {
            "pregunta": row.pregunta, 
            "promedio": float(row.promedio) if row.promedio else 0.0,
            "total_respuestas": row.total_respuestas
        }
        for row in resultados
    ]