from sqlalchemy.orm import Session
from sqlalchemy import text

def get_alumnos_cursando(bd: Session, filtros_json: list = None):
    """
    Retorna lista de diccionarios con info de alumnos, aplicando filtros JIT.
    Join: Inscripciones -> Oferta Academica (para filtrar por Campus/Facultad/Departamento)
    """
    # Base query: Join Inscripciones con Oferta para obtener datos de contexto
    # Simulamos nombre e email basándonos en el ID ya que tabla alumnos no existe.
    sql = """
        SELECT DISTINCT
            i.id_alumno as id,
            'Alumno ' || i.id_alumno as nombre, 
            'alumno' || i.id_alumno || '@uc.edu.py' as email,
            o.facultad,
            o.departamento,
            o.campus
        FROM sapientia.inscripciones i
        JOIN sapientia.oferta_academica o ON 
            i.cod_asignatura = o.cod_asignatura AND 
            i.seccion = o.seccion
    """
    
    where_clauses = []
    params = {}
    
    if filtros_json:
        for i, filtro in enumerate(filtros_json):
            campo = filtro.get("campo", "").lower()
            # Support both legacy 'valor' and new 'valores' (list)
            val = filtro.get("valor")
            vals = filtro.get("valores")
            
            # Normalize to list for uniform handling
            if vals and isinstance(vals, list):
                target_values = [v.lower() for v in vals if isinstance(v, str)]
            elif val:
                 target_values = [str(val).lower()]
            else:
                 continue # No value to filter by

            # Helper to add clause
            param_name = f"vals_{i}"
            params[param_name] = tuple(target_values) # SQLAlchemy requires tuple for IN

            if campo in ["sede", "campus"]:
                where_clauses.append(f"LOWER(o.campus) IN :{param_name}")
                
            elif campo == "facultad":
                where_clauses.append(f"LOWER(o.facultad) IN :{param_name}")
                
            elif campo in ["carrera", "departamento"]:
                where_clauses.append(f"LOWER(o.departamento) IN :{param_name}")

            elif campo == "asignatura":
                where_clauses.append(f"LOWER(o.asignatura) IN :{param_name}")

    if where_clauses:
        sql += " WHERE " + " AND ".join(where_clauses)
        
    query = text(sql)
    query = text(sql)
    result = bd.execute(query, params) # No fetchall, iteramos sobre el cursor
    
    # QA Optimization: Generador
    for row in result:
        yield {
            "id": row.id, 
            "nombre": row.nombre, 
            "email": row.email, 
            "carrera": row.departamento,
            "facultad": row.facultad,
            "campus": row.campus
        }

def get_docentes_activos(bd: Session):
    """
    Retorna lista de docentes activos desde oferta_academica.
    Tabla sapientia.docentes no existe.
    """
    query = text("SELECT DISTINCT id_docente, docente as nombre FROM sapientia.oferta_academica WHERE id_docente IS NOT NULL")
    result = bd.execute(query).fetchall()
    return [
        {"id": row.id_docente, "nombre": row.nombre, "email": ""} # Email no disponible/necesario
        for row in result
    ]

def get_contexto_evaluacion_docente(bd: Session):
    """
    Retorna todas las asignaciones VALIDAS para evaluación docente.
    Join: Inscripciones -> Oferta Academica
    Retorna tuplas (id_alumno, id_docente, contexto_str, metadata_dict)
    """
    query = text("""
        SELECT 
            i.id_alumno,
            o.id_docente,
            o.cod_asignatura as cod_materia,
            o.asignatura as nombre_materia,
            o.seccion as codigo_seccion,
            o.docente as nombre_docente,
            o.departamento,
            'Alumno ' || i.id_alumno as nombre_alumno
        FROM sapientia.inscripciones i
        JOIN sapientia.oferta_academica o ON 
            i.cod_asignatura = o.cod_asignatura AND 
            i.seccion = o.seccion
        WHERE o.id_docente IS NOT NULL
    """)
    
    result = bd.execute(query)
    
    # QA Optimization: Usar generador en lugar de cargar todo en lista
    for row in result:
        # Contexto único: COD_MATERIA-SECCION-ID_DOCENTE
        id_contexto = f"{row.cod_materia}-{row.codigo_seccion}-{row.id_docente}"
        
        meta = {
            "materia": row.nombre_materia,
            "seccion": row.codigo_seccion,
            "docente": row.nombre_docente,
            "alumno": row.nombre_alumno,
            "departamento": row.departamento
        }
        
        yield {
            "id_usuario": row.id_alumno,
            "id_referencia_contexto": id_contexto,
            "metadatos": meta
        }

def get_catalogos(bd: Session):
    """
    Retorna listas unicas de Facultades, Departamentos y Campus.
    """
    facultades = bd.execute(text("SELECT DISTINCT facultad FROM sapientia.oferta_academica ORDER BY facultad")).fetchall()
    departamentos = bd.execute(text("SELECT DISTINCT departamento FROM sapientia.oferta_academica ORDER BY departamento")).fetchall()
    sedes = bd.execute(text("SELECT DISTINCT campus FROM sapientia.oferta_academica ORDER BY campus")).fetchall()
    
    return {
        "facultades": [r[0] for r in facultades if r[0]],
        "departamentos": [r[0] for r in departamentos if r[0]], 
        "sedes": [r[0] for r in sedes if r[0]]
    }
