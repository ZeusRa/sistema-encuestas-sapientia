from sqlalchemy.orm import Session
from sqlalchemy import text

def get_alumnos_cursando(bd: Session, filtros_json: list = None):
    """
    Retorna lista de diccionarios con info de alumnos, aplicando filtros JIT.
    Join: Inscripciones -> Oferta Academica (para filtrar por Campus/Sede)
    """
    # Base query: Join Inscripciones con Oferta para obtener datos de contexto
    # Como no tenemos tabla de alumnos con nombres, simulamos el nombre basándonos en el ID.
    sql = """
        SELECT DISTINCT
            i.id_alumno as id,
            'Alumno ' || i.id_alumno as nombre, 
            'alumno' || i.id_alumno || '@uc.edu.py' as email,
            o.facultad,
            o.departamento as carrera
        FROM sapientia.inscripciones i
        JOIN sapientia.oferta_academica o ON 
            i.cod_asignatura = o.cod_asignatura AND 
            i.seccion = o.seccion
    """
    
    where_clauses = []
    params = {}
    
    if filtros_json:
        # Filtros soportados: "sede" o "campus" -> mapea a columna 'campus' en oferta
        # "facultad" -> 'facultad'
        # "carrera" -> 'departamento' (No existe carrera en oferta, usamos departamento)
        for i, filtro in enumerate(filtros_json):
            campo = filtro.get("campo").lower()
            valor = filtro.get("valor")
            
            if campo in ["sede", "campus"]:
                # Importante: manejo de case insensitive
                where_clauses.append(f"LOWER(o.campus) = LOWER(:val_{i})")
                params[f"val_{i}"] = valor
                
            elif campo == "facultad":
                where_clauses.append(f"LOWER(o.facultad) = LOWER(:val_{i})")
                params[f"val_{i}"] = valor
                
            elif campo == "carrera":
                where_clauses.append(f"LOWER(o.departamento) = LOWER(:val_{i})")
                params[f"val_{i}"] = valor

    if where_clauses:
        sql += " WHERE " + " AND ".join(where_clauses)
        
    query = text(sql)
    result = bd.execute(query, params).fetchall()
    
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

def get_catalogos(bd: Session):
    """
    Retorna listas unicas de Facultades, Carreras (Departamentos) y Campus
    para los filtros del frontend.
    """
    # Consulta optimizada para traer todo de una vez o por partes.
    # Por simplicidad, 3 queries distintos rápidos.
    
    facultades = bd.execute(text("SELECT DISTINCT facultad FROM sapientia.oferta_academica ORDER BY facultad")).fetchall()
    carreras = bd.execute(text("SELECT DISTINCT departamento FROM sapientia.oferta_academica ORDER BY departamento")).fetchall()
    sedes = bd.execute(text("SELECT DISTINCT campus FROM sapientia.oferta_academica ORDER BY campus")).fetchall()
    
    return {
        "facultades": [r[0] for r in facultades if r[0]],
        "carreras": [r[0] for r in carreras if r[0]], # Mapping departamento -> carrera
        "sedes": [r[0] for r in sedes if r[0]]
    }
