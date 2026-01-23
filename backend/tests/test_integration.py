import pytest
from app import modelos
from app.modelos import EstadoEncuesta, EstadoAsignacion
from sqlalchemy import text

# Datos de prueba para el login (Token mockeado o login real si implementamos override)
# Por simplicidad, overrideamos la dependencia de usuario actual en el test o usamos un token.
# En conftest.py no hicimos override de auth, asique asumiremos que el endpoint requiere auth.
# Podemos hacer override de `obtener_usuario_actual` para saltar auth en tests de integracion.

from app.routers.admin import solo_administradores
from app.modelos import UsuarioAdmin, RolAdmin

@pytest.fixture
def admin_auth_override(client):
    """
    Simula un usuario administrador logueado.
    """
    mock_admin = UsuarioAdmin(id_admin=1, nombre_usuario="admin", rol=RolAdmin.ADMINISTRADOR)
    from main import app
    from app.routers.admin import solo_administradores, obtener_usuario_actual
    app.dependency_overrides[solo_administradores] = lambda: mock_admin
    app.dependency_overrides[obtener_usuario_actual] = lambda: mock_admin
    yield
    del app.dependency_overrides[solo_administradores]
    del app.dependency_overrides[obtener_usuario_actual]

def test_flujo_publicacion_encuesta(client, bd, sapientia_data, admin_auth_override):
    """
    Prueba de Integración:
    1. Crear Encuesta (Borrador)
    2. Publicar Encuesta (Leera alumnos de sapientia.inscripciones)
    3. Verificar Asignaciones generadas
    """
    
    # 1. Crear Encuesta
    payload_creacion = {
        "nombre": "Encuesta Integracion 1",
        "descripcion": "Test de flujo completo",
        "mensaje_final": "Gracias",
        "fecha_inicio": "2025-01-01T00:00:00",
        "fecha_fin": "2025-12-31T23:59:59",
        "prioridad": "opcional",
        "acciones_disparadoras": [],
        "activo": True,
        "configuracion": {},
        "reglas": [
             # Regla generica para Ingenieria. 
             # sapientia_data tiene alumnos en Ingenieria (Segun conftest)
            {
                "publico_objetivo": "alumnos",
                "filtros_json": [{"campo": "facultad", "valor": "Ingenieria"}]
            }
        ],
        "preguntas": [
            {
                "texto_pregunta": "¿Te gusta programar?",
                "orden": 1,
                "tipo": "opcion_unica",
                "opciones": [{"texto_opcion": "Si", "orden": 1}, {"texto_opcion": "No", "orden": 2}],
                "activo": True
            }
        ]
    }
    
    response_create = client.post("/admin/encuestas/", json=payload_creacion)
    assert response_create.status_code == 201, f"Error creando encuesta: {response_create.text}"
    data_encuesta = response_create.json()
    id_encuesta = data_encuesta["id"]
    
    # 2. Publicar Encuesta (Trigger Batch Process)
    response_pub = client.post(f"/admin/encuestas/{id_encuesta}/publicar")
    assert response_pub.status_code == 200, f"Error publicando: {response_pub.text}"
    
    # 3. Validar Estado
    data_pub = response_pub.json()
    assert data_pub["estado"] == "en_curso"
    
    # 4. Validar Asignaciones en DB Local (OLTP)
    # Deben haberse creado asignaciones para los alumnos en sapientia
    # En conftest.py insertamos alumnos 100 y 101 en Ingenieria.
    
    # Consultamos directo a la BD (usando modelo local)
    # Nota: `modelos.AsignacionUsuario` apunta schema='encuestas_oltp'
    from sqlalchemy import text
    result = bd.execute(text(f"SELECT COUNT(*) FROM encuestas_oltp.asignacion_usuario WHERE id_encuesta = {id_encuesta}")).scalar()
    
    # Esperamos al menos 1 asignacion (Alumno 100 y 101 estan en inscripciones, ambos Ingenieria segun oferta?)
    # En conftest:
    # 100 -> MAT-101 (Ingenieria)
    # 101 -> MAT-101 (Ingenieria)
    # Entonces deberia haber 2 asignaciones.
    # Pero ojo, asignacion es por usuario unico. Si alumno cursa 2 materias, solo 1 asignacion para encuesta GENERAL.
    # El endpoint `publicar` para "alumnos" (sin contexto especifico de evaluacion docente) asigna por alumno unico.
    
    assert result >= 1, f"Se esperaban asignaciones, se encontraron {result}"
    
    # Verificar detalles de una asignacion
    row = bd.execute(text(f"SELECT id_usuario FROM encuestas_oltp.asignacion_usuario WHERE id_encuesta = {id_encuesta} LIMIT 1")).fetchone()
    assert row[0] in [100, 101]

def test_evaluacion_docente_logica(client, bd, sapientia_data, admin_auth_override):
    """
    Prueba especifica para Evaluacion Docente.
    Debe generar asignaciones CON contexto (Materia-Docente).
    """
    # 1. Crear Encuesta Tipo Evaluacion Docente
    payload = {
        "nombre": "Eval Docente 2025",
        "fecha_inicio": "2025-01-01T00:00:00",
        "fecha_fin": "2025-12-31T00:00:00",
        "prioridad": "evaluacion_docente", # <--- CLAVE
        "acciones_disparadoras": [],
        "reglas": [{"publico_objetivo": "alumnos"}], # Solo alumnos
        "preguntas": [{"texto_pregunta": "Evalua al profe", "orden": 1, "tipo": "texto_libre", "opciones": [], "activo": True}]
    }
    
    res = client.post("/admin/encuestas/", json=payload)
    assert res.status_code == 201
    id_enc = res.json()["id"]
    
    # 2. Publicar
    res_pub = client.post(f"/admin/encuestas/{id_enc}/publicar")
    # En caso de error, mostrar detalle
    assert res_pub.status_code == 200, f"Error pub: {res_pub.text}"
    
    # 3. Verificar Contextos
    # En conftest:
    # Alumno 100 -> MAT-101 (Prof X)
    # Alumno 100 -> PROG-101 (Prof Y)
    # Alumno 101 -> MAT-101 (Prof X)
    # Total asignaciones esperadas: 3
    
    cnt = bd.execute(text(f"SELECT COUNT(*) FROM encuestas_oltp.asignacion_usuario WHERE id_encuesta = {id_enc}")).scalar()
    assert cnt == 3
    
    # Verificar un contexto especifico
    # Contexto formato: COD-SEC-DOC (MAT-101-A-10)
    # Validamos que `id_referencia_contexto` no sea nulo
    nulls = bd.execute(text(f"SELECT COUNT(*) FROM encuestas_oltp.asignacion_usuario WHERE id_encuesta = {id_enc} AND id_referencia_contexto IS NULL")).scalar()
    assert nulls == 0

def test_actualizar_encuesta_con_filtros(client, bd, admin_auth_override):
    """
    Test de Regresión: Verifica que al actualizar una encuesta, los filtros (reglas) se guarden correctamente.
    Bug Previo: PUT ignoraba el campo filtros_json al recrear las reglas.
    """
    # 1. Crear Encuesta Inicial
    payload_creacion = {
        "nombre": "Encuesta Filtros",
        "descripcion": "Test Save Filters",
        "fecha_inicio": "2025-01-01T00:00:00",
        "fecha_fin": "2025-12-31T23:59:59",
        "prioridad": "opcional",
        "acciones_disparadoras": [],
        "activo": True,
        "configuracion": {},
        "reglas": [{"publico_objetivo": "alumnos", "filtros_json": []}],
        "preguntas": [{"texto_pregunta": "P1", "orden": 1, "tipo": "texto_libre", "opciones": [], "activo": True}]
    }
    
    res_crear = client.post("/admin/encuestas/", json=payload_creacion)
    print("DEBUG RESPONSE:", res_crear.json())
    assert res_crear.status_code == 201
    id_encuesta = res_crear.json()["id"]
    
    # 2. Actualizar Encuesta AGREGANDO filtros
    payload_update = res_crear.json()
    # Modificamos la regla para agregar un filtro
    payload_update["reglas"][0]["filtros_json"] = [
        {"id": 123, "campo": "carrera", "regla": "es", "valores": ["Derecho"]}
    ]
    
    res_update = client.put(f"/admin/encuestas/{id_encuesta}", json=payload_update)
    assert res_update.status_code == 200
    
    # 3. Verificar Persistencia (Recargar desde GET)
    res_get = client.get(f"/admin/encuestas/{id_encuesta}")
    data_get = res_get.json()
    
    filtros = data_get["reglas"][0]["filtros_json"]
    assert filtros is not None, "filtros_json es None"
    assert len(filtros) == 1, f"Se esperaba 1 filtro, se encontraron {len(filtros)}"
    assert filtros[0]["valores"][0] == "Derecho", "El valor del filtro no coincide"

