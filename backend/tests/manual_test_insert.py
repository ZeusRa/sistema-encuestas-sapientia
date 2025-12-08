import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from main import app
from app.routers.admin import solo_administradores
from app.modelos import UsuarioAdmin, RolAdmin
from unittest.mock import MagicMock
import json

# Setup Mock
def mock_admin():
    user = MagicMock(spec=UsuarioAdmin)
    user.id_admin = 1
    user.nombre_usuario = "admin_test"
    user.rol = RolAdmin.ADMINISTRADOR
    return user

app.dependency_overrides[solo_administradores] = mock_admin

client = TestClient(app)

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

print("Enviando payload:", json.dumps(payload, indent=2))
response = client.post("/admin/encuestas/", json=payload)
print("Status Code:", response.status_code)
print("Response Body:", response.text)
