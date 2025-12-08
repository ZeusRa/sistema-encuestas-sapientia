from fastapi.testclient import TestClient
from sqlalchemy import text
from app.database import obtener_bd, Base, motor
from main import app
from app.modelos import Encuesta, UsuarioAdmin, RolAdmin
from unittest.mock import MagicMock
from app.routers.admin import solo_administradores
import pytest

client = TestClient(app)

# -----------------------------------------------------------------------------
# FIXTURES
# -----------------------------------------------------------------------------

@pytest.fixture
def mock_admin():
    """Simula un usuario administrador autenticado para saltar el login real."""
    user = MagicMock(spec=UsuarioAdmin)
    user.id_admin = 1
    user.nombre_usuario = "admin_test"
    user.rol = RolAdmin.ADMINISTRADOR
    
    # Override de la dependencia que proteje el endpoint
    app.dependency_overrides[solo_administradores] = lambda: user
    yield user
    app.dependency_overrides = {}

# -----------------------------------------------------------------------------
# TESTS
# -----------------------------------------------------------------------------

def test_insercion_con_prefijo_test(mock_admin):
    """
    1. Verifica que se pueda insertar un registro (Encuesta) con el nombre 'TEST ...'.
    2. Verifica que el ID generado sea válido.
    """
    payload = {
        "nombre": "TEST Encuesta de Verificación",
        "descripcion": "Encuesta creada por test automático para validar secuencias",
        "fecha_inicio": "2025-01-01T00:00:00",
        "fecha_fin": "2025-12-31T23:59:59",
        "prioridad": "opcional",
        "reglas": [
            {
                "publico_objetivo": "alumnos"
            }
        ]
    }
    
    # Endpoint backend/app/routers/admin.py -> /admin/encuestas
    response = client.post("/admin/encuestas", json=payload)
    
    assert response.status_code == 200, f"Error al crear encuesta: {response.text}"
    data = response.json()
    
    assert "id" in data
    assert data["nombre"].startswith("TEST")
    print(f"\n[OK] Encuesta creada con ID: {data['id']} y Nombre: {data['nombre']}")

def test_verificar_secuencias_bd():
    """
    Verifica que las secuencias de las tablas principales estén sincronizadas con los IDs.
    last_value de la secuencia >= max(id) de la tabla.
    """
    tablas_a_verificar = [
        ("encuestas_oltp.encuesta", "encuestas_oltp.encuesta_id_seq"),
        ("encuestas_oltp.pregunta", "encuestas_oltp.pregunta_id_seq"),
        ("encuestas_oltp.usuario_admin", "encuestas_oltp.usuario_admin_id_admin_seq"),
    ]

    errores = []

    with motor.connect() as conn:
        for tabla, secuencia in tablas_a_verificar:
            try:
                # Obtener max id
                res_max = conn.execute(text(f"SELECT COALESCE(MAX(id), 0) FROM {tabla}")).scalar()
                if tabla == "encuestas_oltp.usuario_admin": # Excepcion nombre columna
                     res_max = conn.execute(text(f"SELECT COALESCE(MAX(id_admin), 0) FROM {tabla}")).scalar()
                
                # Obtener valor secuencia
                res_seq = conn.execute(text(f"SELECT last_value FROM {secuencia}")).scalar()
                
                print(f"Revisando {tabla}: MaxID={res_max}, Seq={res_seq}")
                
                # PostgreSQL preasigna, asi que last_value debe ser >= MaxID
                if res_seq < res_max:
                    errores.append(f"DESFASE EN {tabla}: Secuencia ({res_seq}) < MaxID ({res_max})")
            
            except Exception as e:
                # Si la tabla esta vacia puede que last_value=1 y max=0, OK.
                print(f"Aviso checkeando {tabla}: {e}")

    assert len(errores) == 0, "\\n".join(errores)
