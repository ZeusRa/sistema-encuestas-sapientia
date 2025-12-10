from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

# ==========================================
# TEST: Reportes y Analítica
# ==========================================

# ==========================================
# MOCKING AUTH
# ==========================================
# Mockeamos el usuario para todos los tests de este archivo
from app.routers.admin import obtener_usuario_actual

def mock_obtener_usuario_actual():
    return {"sub": "testuser", "rol": "admin"}

app.dependency_overrides[obtener_usuario_actual] = mock_obtener_usuario_actual

# ==========================================
# TEST: Reportes y Analítica
# ==========================================

def test_reportes_respuestas_tabla_structure():
    """
    Verifica que el endpoint de tabla de respuestas devuelva 200 OK.
    """
    response = client.get("/reportes/respuestas-tabla")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_reportes_distribucion_structure():
    """
    Verifica endpoint de distribución.
    """
    response = client.get("/reportes/distribucion-respuestas")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_reportes_respuestas_tabla_ok():
    """
    Prueba con auth mockeado.
    """
    response = client.get("/reportes/respuestas-tabla?limit=5")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    
    # Si devuelve algo, verificar estructura
    data = response.json()
    if len(data) > 0:
        item = data[0]
        assert "texto_pregunta" in item
        assert "nombre_encuesta" in item
        assert "respuesta_texto" in item

def test_reportes_analisis_texto_ok():
    response = client.get("/reportes/analisis-texto")
    print(response.json())
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_reportes_distribucion_ok():
    response = client.get("/reportes/distribucion-respuestas")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    
    data = response.json()
    if len(data) > 0:
        item = data[0]
        assert "pregunta" in item
        assert "opciones" in item

def test_reportes_filtro_nombre_encuesta():
    """
    Prueba que el filtro nombre_encuesta no rompa el query.
    """
    response = client.get("/reportes/respuestas-tabla?nombre_encuesta=EncuestaTest")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
