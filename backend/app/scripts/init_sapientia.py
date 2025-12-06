import sys
import os
import random
from datetime import datetime
from sqlalchemy import create_engine, text, MetaData, Table, Column, Integer, String, Date, ForeignKey, Boolean
from sqlalchemy.orm import sessionmaker

# Add the parent directory to sys.path to allow importing from app
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from app.database import URL_BASE_DATOS

def init_sapientia_schema():
    print(f"Connecting to database...")
    engine = create_engine(URL_BASE_DATOS)
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        print("Creating 'sapientia' schema if not exists...")
        session.execute(text("CREATE SCHEMA IF NOT EXISTS sapientia;"))
        session.commit()

        metadata = MetaData(schema="sapientia")

        # Define tables
        alumnos = Table('alumnos', metadata,
            Column('id', Integer, primary_key=True),
            Column('nombre', String(100)),
            Column('email', String(100)),
            Column('carrera', String(100))
        )

        docentes = Table('docentes', metadata,
            Column('id', Integer, primary_key=True),
            Column('nombre', String(100)),
            Column('email', String(100))
        )

        asignaturas = Table('asignaturas', metadata,
            Column('id', Integer, primary_key=True),
            Column('codigo', String(20)),
            Column('nombre', String(100)),
            Column('semestre', Integer)
        )

        secciones = Table('secciones', metadata,
            Column('id', Integer, primary_key=True),
            Column('id_asignatura', Integer, ForeignKey('sapientia.asignaturas.id')),
            Column('codigo_seccion', String(10)),
            Column('id_docente_principal', Integer, ForeignKey('sapientia.docentes.id'))
        )

        inscripciones = Table('inscripciones', metadata,
            Column('id', Integer, primary_key=True),
            Column('id_alumno', Integer, ForeignKey('sapientia.alumnos.id')),
            Column('id_seccion', Integer, ForeignKey('sapientia.secciones.id')),
            Column('fecha_inscripcion', Date)
        )

        print("Creating tables in 'sapientia' schema...")
        metadata.create_all(engine)

        # Clear existing data
        print("Clearing existing mock data...")
        session.execute(text("TRUNCATE TABLE sapientia.inscripciones CASCADE"))
        session.execute(text("TRUNCATE TABLE sapientia.secciones CASCADE"))
        session.execute(text("TRUNCATE TABLE sapientia.asignaturas CASCADE"))
        session.execute(text("TRUNCATE TABLE sapientia.docentes CASCADE"))
        session.execute(text("TRUNCATE TABLE sapientia.alumnos CASCADE"))
        session.commit()

        # Seed Data
        print("Seeding mock data...")
        
        # Alumnos
        lista_alumnos = [
            {"id": 1, "nombre": "Juan Alumno", "email": "juan@alu.edu", "carrera": "Ingeniería Informática"},
            {"id": 2, "nombre": "Maria Estudiante", "email": "maria@alu.edu", "carrera": "Ingeniería Informática"},
            {"id": 3, "nombre": "Pedro Universitario", "email": "pedro@alu.edu", "carrera": "Derecho"},
            {"id": 4, "nombre": "Ana Academica", "email": "ana@alu.edu", "carrera": "Derecho"},
        ]
        session.execute(alumnos.insert(), lista_alumnos)

        # Docentes
        lista_docentes = [
            {"id": 101, "nombre": "Prof. Einstein", "email": "albert@prof.edu"},
            {"id": 102, "nombre": "Prof. Curie", "email": "marie@prof.edu"},
            {"id": 103, "nombre": "Prof. Newton", "email": "isaac@prof.edu"},
        ]
        session.execute(docentes.insert(), lista_docentes)

        # Asignaturas
        lista_asignaturas = [
            {"id": 501, "codigo": "FIS101", "nombre": "Física I", "semestre": 1},
            {"id": 502, "codigo": "CAL101", "nombre": "Cálculo I", "semestre": 1},
            {"id": 503, "codigo": "DER101", "nombre": "Derecho Romano", "semestre": 1},
        ]
        session.execute(asignaturas.insert(), lista_asignaturas)

        # Secciones (Asignatura + Docente)
        lista_secciones = [
            {"id": 1001, "id_asignatura": 501, "codigo_seccion": "A", "id_docente_principal": 101}, # Fisica - Einstein
            {"id": 1002, "id_asignatura": 501, "codigo_seccion": "B", "id_docente_principal": 103}, # Fisica - Newton
            {"id": 1003, "id_asignatura": 502, "codigo_seccion": "A", "id_docente_principal": 103}, # Calculo - Newton
            {"id": 1004, "id_asignatura": 503, "codigo_seccion": "U", "id_docente_principal": 102}, # Derecho - Curie
        ]
        session.execute(secciones.insert(), lista_secciones)

        # Inscripciones (Alumno -> Seccion)
        lista_inscripciones = [
            # Juan (Inf) -> Fisica A, Calculo A
            {"id_alumno": 1, "id_seccion": 1001, "fecha_inscripcion": datetime.now()},
            {"id_alumno": 1, "id_seccion": 1003, "fecha_inscripcion": datetime.now()},
            
            # Maria (Inf) -> Fisica B, Calculo A
            {"id_alumno": 2, "id_seccion": 1002, "fecha_inscripcion": datetime.now()},
            {"id_alumno": 2, "id_seccion": 1003, "fecha_inscripcion": datetime.now()},
            
            # Pedro (Der) -> Derecho U
            {"id_alumno": 3, "id_seccion": 1004, "fecha_inscripcion": datetime.now()},

            # Ana (Der) -> Derecho U
            {"id_alumno": 4, "id_seccion": 1004, "fecha_inscripcion": datetime.now()},
        ]
        session.execute(inscripciones.insert(), lista_inscripciones)

        session.commit()
        print("Sapientia Logic Simulation Environment Initialized Successfully.")

    except Exception as e:
        session.rollback()
        print(f"Error initializing sapientia schema: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()

if __name__ == "__main__":
    init_sapientia_schema()
