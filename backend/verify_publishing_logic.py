import urllib.request
import urllib.parse
import json
import sys

BASE_URL = "http://localhost:8000"
TOKEN = None

def login():
    global TOKEN
    url = f"{BASE_URL}/token"
    data = urllib.parse.urlencode({
        "username": "admin",
        "password": "admin123"
    }).encode()
    
    req = urllib.request.Request(url, data=data, method="POST")
    req.add_header("Content-Type", "application/x-www-form-urlencoded")
    
    try:
        with urllib.request.urlopen(req) as response:
            res_json = json.loads(response.read().decode())
            TOKEN = res_json["access_token"]
            print("Login success.")
            return True
    except Exception as e:
        print(f"Login failed: {e}")
        return False

def make_request(endpoint, method="GET", data=None):
    url = f"{BASE_URL}{endpoint}"
    if data:
        json_data = json.dumps(data).encode()
        req = urllib.request.Request(url, data=json_data, method=method)
        req.add_header("Content-Type", "application/json")
    else:
        req = urllib.request.Request(url, method=method)
    
    req.add_header("Authorization", f"Bearer {TOKEN}")
    
    try:
        with urllib.request.urlopen(req) as response:
            return response.status, json.loads(response.read().decode())
    except urllib.error.HTTPError as e:
        print(f"Error {e.code} for {url}: {e.read().decode()}")
        return e.code, None
    except Exception as e:
        print(f"Error requesting {url}: {e}")
        return 500, None

def test_filters_refactor():
    print("\n--- Testing Filters Refactor (Departamento) ---")
    # 1. Check /sapientia/departamentos
    status, data = make_request("/sapientia/departamentos")
    if status == 200:
        print(f"GET /sapientia/departamentos: OK. Count: {len(data)}")
        if len(data) > 0:
            print(f"Example dept: {data[0]}")
    else:
        print("GET /sapientia/departamentos FAILED")

    # 2. Check /sapientia/carreras (Should be gone or 404/405 if renamed, or if I didn't verify it was removed from file)
    # Actually I used 'Replace' so it should be gone.
    status, _ = make_request("/sapientia/carreras")
    if status == 404:
        print("GET /sapientia/carreras: OK (Correctly 404 not found)")
    else:
        print(f"GET /sapientia/carreras returned {status} (Unexpected)")

def test_publishing_logic():
    print("\n--- Testing Publishing Logic ---")
    
    # 1. Create Draft Survey with Rule
    # Rule: Facultad=ingenieria, Departamento=Informatica (example)
    # Need to know valid values.
    status, depts = make_request("/sapientia/departamentos")
    dept_val = depts[0] if depts else "Ingeniería Informática"
    
    payload = {
        "nombre": "Encuesta Test Publishing Auto",
        "descripcion": "Test auto",
        "mensaje_final": "Gracias",
        "fecha_inicio": "2025-01-01T00:00:00",
        "fecha_fin": "2025-12-31T00:00:00",
        "prioridad": "opcional",
        "activo": True,
        "acciones_disparadoras": ["al_iniciar_sesion"],
        "configuracion": {},
        "reglas": [
            {
                "id_facultad": None,
                "id_carrera": None, 
                "id_asignatura": None,
                "publico_objetivo": "alumnos",
                "filtros_json": [
                    {"campo": "departamento", "valor": dept_val} # Using new terminology
                ]
            }
        ],
        "preguntas": []
    }
    
    status, survey = make_request("/admin/encuestas/", "POST", payload)
    if status != 201:
        print("Failed to create survey")
        return
    
    survey_id = survey["id"]
    print(f"Created Survey ID: {survey_id}")
    
    # 2. Publish Survey
    print("Publishing survey...")
    status, published_survey = make_request(f"/admin/encuestas/{survey_id}/publicar", "POST")
    if status == 200:
        print("Survey Published Successfully")
        print(f"State: {published_survey['estado']}")
    else:
        print("Failed to publish survey")
        return

    # 3. Verify Assignments (Requires direct DB check or endpoint? Admin dashboard metrics?)
    # We can use /reportes-avanzados/dashboard/kpis?encuesta_id=...
    status, kpis = make_request(f"/reportes-avanzados/dashboard/kpis?encuesta_id={survey_id}")
    if status == 200:
        print("KPIs fetched.")
        print(f"Total Asignaciones: {kpis['total_asignaciones']}")
        if kpis['total_asignaciones'] > 0:
            print("SUCCESS: Assignments generated!")
        else:
            print("WARNING: No assignments generated. Check if 'get_alumnos_cursando' returned data.")
    else:
        print("Failed to fetch KPIs")

if __name__ == "__main__":
    if login():
        test_filters_refactor()
        test_publishing_logic()
