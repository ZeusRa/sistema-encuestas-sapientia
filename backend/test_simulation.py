

# URL base (internal docker network or localhost if exposed)
# Assuming run provided 'docker-compose run' so localhost is accessible if ports mapped, 
# OR we run this script INSIDE docker.
# We'll run inside docker.

from app.database import SesionLocal
from app.routers import admin_tecnico
from app import modelos
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_simulacion():
    # 1. Obtener una encuesta existente (o crear)
    # Usamos ID 14 del JIT test si existe, o ID 1
    encuesta_id = 14
    
    # 2. Mock Admin Auth (Dependency override needed?)
    # TestClient bypasses auth middleware? No.
    # We need to override dependency.
    
    from app.routers.auth import obtener_usuario_actual
    def mock_auth():
        return modelos.UsuarioAdmin(id_admin=1, nombre_usuario="admin", rol=modelos.RolAdmin.ADMINISTRADOR)
    
    app.dependency_overrides[obtener_usuario_actual] = mock_auth

    # 3. Request Simulación
    payload = {
        "id_encuesta": encuesta_id,
        "id_usuario": 10005635,
        "crear_asignacion": True
    }
    
    print(f"Enviando solicitud de simulación para Encuesta {encuesta_id}...")
    try:
        resp = client.post("/admin/tecnico/simulacion", json=payload)
        print(f"Status Code: {resp.status_code}")
        print(f"Response: {resp.json()}")
        
        if resp.status_code == 200 and resp.json().get("exito"):
            print("✅ Simulación Exitosa")
        else:
            print("❌ Fallo en Simulación")
    except Exception as e:
        print(f"❌ Excepción: {e}")

if __name__ == "__main__":
    from app import modelos # Fix import path if needed inside container
    test_simulacion()
