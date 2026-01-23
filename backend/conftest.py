import pytest
from sqlalchemy import create_engine, text, JSON
from sqlalchemy.orm import sessionmaker, Session
from fastapi.testclient import TestClient

# PATCH: Reemplazar tipos de PostgreSQL no soportados por SQLite
import sqlalchemy.dialects.postgresql
sqlalchemy.dialects.postgresql.JSONB = JSON
sqlalchemy.dialects.postgresql.UUID = sqlalchemy.types.String # Si se usa UUID

from main import app
from app.database import Base, obtener_bd
from app import modelos

# Configuración de SQLite en memoria
# Check_same_thread=False es necesario para que el cliente de prueba y app compartan hilo/conexión en tests simples
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args={"check_same_thread": False}
)

# =============================================================================
# CONFIGURACION DE SCHEMAS Y TABLAS
# =============================================================================

@pytest.fixture(scope="session", autouse=True)
def setup_databases():
    """
    Simula los esquemas de PostgreSQL usando 'ATTACH DATABASE' de SQLite.
    Esto permite que queries como 'SELECT * FROM sapientia.tabla' funcionen.
    """
    with engine.connect() as connection:
        # 1. Crear esquemas adjuntos (Attached Databases)
        connection.execute(text("ATTACH DATABASE ':memory:' AS encuestas_oltp"))
        connection.execute(text("ATTACH DATABASE ':memory:' AS encuestas_olap"))
        connection.execute(text("ATTACH DATABASE ':memory:' AS sapientia"))
        
        # 2. Crear tablas del modelo (OLTP y OLAP)
        Base.metadata.create_all(bind=engine)

        # 3. Crear tablas MANUALES de Sapientia
        connection.execute(text("""
            CREATE TABLE sapientia.oferta_academica (
                id_docente INTEGER,
                docente TEXT,
                cod_asignatura TEXT,
                asignatura TEXT,
                seccion TEXT,
                facultad TEXT,
                departamento TEXT,
                campus TEXT,
                semestre INTEGER,
                anho INTEGER
            )
        """))
        
        connection.execute(text("""
            CREATE TABLE sapientia.inscripciones (
                id_alumno INTEGER,
                cod_asignatura TEXT,
                seccion TEXT,
                periodo TEXT
            )
        """))
        connection.commit()

# =============================================================================
# SESION Y CLIENTE
# =============================================================================

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def bd():
    """
    Entrega una sesión de base de datos para cada test.
    Hace rollback al final para aislar tests.
    """
    connection = engine.connect()
    transaction = connection.begin()
    
    try:
        connection.execute(text("SELECT 1 FROM sapientia.oferta_academica LIMIT 1"))
    except:
        connection.execute(text("ATTACH DATABASE ':memory:' AS encuestas_oltp"))
        connection.execute(text("ATTACH DATABASE ':memory:' AS encuestas_olap"))
        connection.execute(text("ATTACH DATABASE ':memory:' AS sapientia"))

    session = TestingSessionLocal(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture(scope="function")
def client(bd):
    """
    Cliente API que sobreescribe la dependencia de BD.
    """
    def override_get_db():
        try:
            yield bd
        finally:
            pass 
    
    app.dependency_overrides[obtener_bd] = override_get_db
    yield TestClient(app)
    app.dependency_overrides = {}

# =============================================================================
# FIXTURES DE DATOS (DATA SEEDS)
# =============================================================================

@pytest.fixture
def sapientia_data(bd: Session):
    """
    Puebla el esquema 'sapientia' con datos de prueba.
    """
    bd.execute(text("DELETE FROM sapientia.inscripciones"))
    bd.execute(text("DELETE FROM sapientia.oferta_academica"))
    
    bd.execute(text("""
        INSERT INTO sapientia.oferta_academica 
        (id_docente, docente, cod_asignatura, asignatura, seccion, facultad, departamento, campus)
        VALUES 
        (10, 'Profesor X', 'MAT-101', 'Matematicas I', 'A', 'Ingenieria', 'Ciencias Basicas', 'Central'),
        (11, 'Profesor Y', 'PROG-101', 'Programacion I', 'B', 'Ingenieria', 'Informatica', 'Central')
    """))
    
    bd.execute(text("""
        INSERT INTO sapientia.inscripciones (id_alumno, cod_asignatura, seccion)
        VALUES 
        (100, 'MAT-101', 'A'),
        (100, 'PROG-101', 'B'),
        (101, 'MAT-101', 'A') 
    """))
    
    bd.commit()
    return True
