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

# -----------------------------------------------------------------------------
# NUEVOS ENDPOINTS ANALÍTICA AVANZADA (OLAP)
# -----------------------------------------------------------------------------

@router.get("/respuestas-tabla", response_model=List[schemas.ReporteTablaRespuesta])
def reporte_tabla_respuestas(
    bd: Session = Depends(obtener_bd),
    usuario: dict = Depends(obtener_usuario_actual),
    anho: int = None,
    semestre: int = None,
    facultad: str = None,
    carrera: str = None,
    docente: str = None,
    asignatura: str = None,
    nombre_encuesta: str = None,
    page: int = 1,
    limit: int = 100
):
    """
    Retorna una tabla plana de hechos_respuestas con JOIN a dimensiones.
    Soporta filtros y paginación.
    """
    offset = (page - 1) * limit
    
    # Construcción dinámica de filtros
    filtros = []
    if anho:
        filtros.append(f"t.anho = {anho}")
    if semestre:
        filtros.append(f"t.semestre = {semestre}")
    if facultad and facultad != 'Todos':
        filtros.append(f"u.nombre_facultad = '{facultad}'")
    if carrera and carrera != 'Todos':
        filtros.append(f"u.nombre_carrera = '{carrera}'")
    if docente and docente != 'Todos':
        filtros.append(f"c.nombre_profesor = '{docente}'") # Asumiendo nombre_profesor en dim_contexto
    if asignatura and asignatura != 'Todos':
        filtros.append(f"c.nombre_asignatura = '{asignatura}'")
    if nombre_encuesta:
        filtros.append(f"p.nombre_encuesta = '{nombre_encuesta}'")

    where_clause = "WHERE 1=1"
    if filtros:
        where_clause += " AND " + " AND ".join(filtros)

    query = text(f"""
        SELECT 
            h.id_hecho,
            t.fecha,
            p.texto_pregunta,
            p.nombre_encuesta,
            h.respuesta_texto,
            u.nombre_facultad as facultad,
            u.nombre_carrera as carrera,
            c.nombre_asignatura as asignatura
        FROM encuestas_olap.hechos_respuestas h
        JOIN encuestas_olap.dim_tiempo t ON h.id_dim_tiempo = t.id_dim_tiempo
        JOIN encuestas_olap.dim_ubicacion u ON h.id_dim_ubicacion = u.id_dim_ubicacion
        JOIN encuestas_olap.dim_pregunta p ON h.id_dim_pregunta = p.id_dim_pregunta
        LEFT JOIN encuestas_olap.dim_contexto_academico c ON h.id_dim_contexto = c.id_dim_contexto
        {where_clause}
        ORDER BY h.id_hecho DESC
        LIMIT {limit} OFFSET {offset}
    """)
    
    try:
        resultados = bd.execute(query).fetchall()
    except Exception as e:
        # En caso de error (e.g., tabla no existe aun por ETL pendiente), devolvemos lista vacía
        print(f"Error consulta OLAP: {e}")
        return []
    
    return [
        {
            "id_hecho": row.id_hecho,
            "fecha": str(row.fecha),
            "texto_pregunta": row.texto_pregunta,
            "nombre_encuesta": row.nombre_encuesta,
            "respuesta_texto": row.respuesta_texto,
            "facultad": row.facultad,
            "carrera": row.carrera,
            "asignatura": row.asignatura
        }
        for row in resultados
    ]

@router.get("/analisis-texto", response_model=List[schemas.ReporteNubePalabras])
def reporte_nube_palabras(
    bd: Session = Depends(obtener_bd),
    usuario: dict = Depends(obtener_usuario_actual),
    anho: int = None,
    facultad: str = None,
    nombre_encuesta: str = None
):
    """
    Analiza respuestas de preguntas de texto (donde respuesta_numerica IS NULL).
    """
    filtros = ["h.respuesta_numerica IS NULL"] # Solo texto
    filtros.append("length(h.respuesta_texto) > 3") # Ignorar respuestas muy cortas
    
    if anho:
        filtros.append(f"t.anho = {anho}")
    if facultad and facultad != 'Todos':
        filtros.append(f"u.nombre_facultad = '{facultad}'")
    if nombre_encuesta:
        filtros.append(f"h.id_dim_pregunta IN (SELECT id_dim_pregunta FROM encuestas_olap.dim_pregunta WHERE nombre_encuesta = '{nombre_encuesta}')")
        
    where_clause = "WHERE " + " AND ".join(filtros)
    
    query = text(f"""
        SELECT h.respuesta_texto
        FROM encuestas_olap.hechos_respuestas h
        JOIN encuestas_olap.dim_tiempo t ON h.id_dim_tiempo = t.id_dim_tiempo
        JOIN encuestas_olap.dim_ubicacion u ON h.id_dim_ubicacion = u.id_dim_ubicacion
        {where_clause}
        LIMIT 2000
    """)
    
    try:
        filas = bd.execute(query).fetchall()
    except Exception:
        return []
    
    # Análisis simple de frecuencia en Python
    from collections import Counter
    import re
    
    textos = [row.respuesta_texto for row in filas if row.respuesta_texto]
    todo_texto = " ".join(textos).lower()
    
    # Limpieza básica
    palabras = re.findall(r'\w+', todo_texto)
    stopwords = {'de', 'la', 'que', 'el', 'en', 'y', 'a', 'los', 'del', 'se', 'las', 'por', 'un', 'para', 'con', 'no', 'una', 'su', 'al', 'lo', 'como', 'mas', 'pero', 'sus', 'le', 'ya', 'o', 'fue', 'este', 'ha', 'si', 'porque', 'esta', 'son', 'mi', 'sin', 'sobre', 'todo', 'tambien', 'me', 'hasta', 'hay', 'donde', 'quien', 'desde', 'nos', 'durante', 'todos', 'uno', 'les', 'ni', 'contra', 'otros', 'ese', 'eso', 'ante', 'ellos', 'e', 'esto', 'mi', 'antes', 'algunos', 'que', 'unos', 'yo', 'otro', 'otras', 'otra', 'el', 'ella', 'cual', 'poco', 'ella', 'estar', 'estos', 'algunas', 'algo', 'nosotros', 'mi', 'mis', 'tu', 'te', 'ti', 'tu', 'tus', 'ellas', 'nosotras', 'vosotros', 'vosotras', 'os', 'mio', 'mia', 'mios', 'mias', 'tuyo', 'tuya', 'tuyos', 'tuyas', 'suyo', 'suya', 'suyos', 'suyas', 'nuestro', 'nuestra', 'nuestros', 'nuestras', 'vuestro', 'vuestra', 'vuestros', 'vuestras', 'es', 'soy', 'eres', 'somos', 'sois', 'estoy', 'estas', 'estamos', 'estais', 'estan'}
    
    palabras_filtradas = [p for p in palabras if p not in stopwords and len(p) > 3]
    
    contador = Counter(palabras_filtradas)
    top_50 = contador.most_common(50)
    
    return [{"text": p[0], "value": p[1]} for p in top_50]

@router.get("/distribucion-respuestas", response_model=List[schemas.ReporteDistribucion])
def reporte_distribucion(
    bd: Session = Depends(obtener_bd),
    usuario: dict = Depends(obtener_usuario_actual),
    anho: int = None,
    facultad: str = None,
    nombre_encuesta: str = None
):
    """
    Agrupa respuestas por pregunta. Ideal para gráficos apilados.
    Solo considera preguntas que NO sean abiertas (respuesta_numerica NOT NULL o categorizable).
    Para simplificar, usamos el hecho de que si es selección, 'respuesta_texto' contiene la opción.
    """
    filtros = []
    
    if anho:
        filtros.append(f"t.anho = {anho}")
    if facultad and facultad != 'Todos':
        filtros.append(f"u.nombre_facultad = '{facultad}'")
    if nombre_encuesta:
        filtros.append(f"p.nombre_encuesta = '{nombre_encuesta}'")
    
    where_clause = "WHERE 1=1 " 
    if filtros:
        where_clause += " AND " + " AND ".join(filtros)
        
    query = text(f"""
        SELECT 
            p.texto_pregunta,
            h.respuesta_texto,
            COUNT(*) as conteo
        FROM encuestas_olap.hechos_respuestas h
        JOIN encuestas_olap.dim_tiempo t ON h.id_dim_tiempo = t.id_dim_tiempo
        JOIN encuestas_olap.dim_ubicacion u ON h.id_dim_ubicacion = u.id_dim_ubicacion
        JOIN encuestas_olap.dim_pregunta p ON h.id_dim_pregunta = p.id_dim_pregunta
        {where_clause}
        GROUP BY p.texto_pregunta, h.respuesta_texto
        ORDER BY p.texto_pregunta
    """)
    
    try:
        filas = bd.execute(query).fetchall()
    except Exception:
        return []
    
    # Procesar en Python para estructura {"pregunta": X, opciones: {A: 10, B: 20}}
    agrupado = {}
    
    for row in filas:
        preg = row.texto_pregunta
        resp = row.respuesta_texto
        cnt = row.conteo
        
        if preg not in agrupado:
            agrupado[preg] = {"total": 0, "conteos": {}}
        
        agrupado[preg]["conteos"][resp] = cnt
        agrupado[preg]["total"] += cnt
        
    resultado_final = []
    for preg, datos in agrupado.items():
        total = datos["total"]
        if total == 0: continue
        
        # Calcular porcentajes
        opciones_pct = {}
        for resp, cnt in datos["conteos"].items():
            pct = round((cnt / total) * 100, 1)
            opciones_pct[resp] = pct
            
        resultado_final.append({
            "pregunta": preg,
            "opciones": opciones_pct
        })
        
    return resultado_final