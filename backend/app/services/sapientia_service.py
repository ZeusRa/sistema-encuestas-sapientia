from sqlalchemy.orm import Session
from sqlalchemy import text

def get_alumnos_cursando(bd: Session):
    """
    Retorna lista de diccionarios con info de alumnos activos.
    Simula: SELECT * FROM sapientia.alumnos
    """
    query = text("SELECT id, nombre, email, carrera FROM sapientia.alumnos")
    result = bd.execute(query).fetchall()
    return [
        {"id": row.id, "nombre": row.nombre, "email": row.email, "carrera": row.carrera}
        for row in result
    ]

def get_docentes_activos(bd: Session):
    """
    Retorna lista de docentes activos.
    """
    query = text("SELECT id, nombre, email FROM sapientia.docentes")
    result = bd.execute(query).fetchall()
    return [
        {"id": row.id, "nombre": row.nombre, "email": row.email}
        for row in result
    ]

def get_contexto_evaluacion_docente(bd: Session):
    """
    Retorna todas las asignaciones VALIDAS para evaluación docente.
    Join: Inscripciones -> Secciones -> Asignaturas -> Docentes -> Alumnos
    Retorna tuplas (id_alumno, id_docente, contexto_str, metadata_dict)
    """
    query = text("""
        SELECT 
            i.id_alumno,
            s.id_docente_principal as id_docente,
            a.codigo as cod_materia,
            a.nombre as nombre_materia,
            s.codigo_seccion,
            d.nombre as nombre_docente,
            al.nombre as nombre_alumno
        FROM sapientia.inscripciones i
        JOIN sapientia.secciones s ON i.id_seccion = s.id
        JOIN sapientia.asignaturas a ON s.id_asignatura = a.id
        JOIN sapientia.docentes d ON s.id_docente_principal = d.id
        JOIN sapientia.alumnos al ON i.id_alumno = al.id
    """)
    
    result = bd.execute(query).fetchall()
    asignaciones_pendientes = []
    
    for row in result:
        # Contexto único: COD_MATERIA-SECCION-ID_DOCENTE
        # Ejemplo: FIS101-A-101
        id_contexto = f"{row.cod_materia}-{row.codigo_seccion}-{row.id_docente}"
        
        meta = {
            "materia": row.nombre_materia,
            "seccion": row.codigo_seccion,
            "docente": row.nombre_docente,
            "alumno": row.nombre_alumno
        }
        
        asignaciones_pendientes.append({
            "id_usuario": row.id_alumno,
            "id_referencia_contexto": id_contexto,
            "metadatos": meta
        })
        
    return asignaciones_pendientes
