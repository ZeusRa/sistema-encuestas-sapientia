import urllib.request
import urllib.parse
import json
import sys

BASE_URL = "http://localhost:8001"
TOKEN = None

def login():
    global TOKEN
    url = f"{BASE_URL}/token"
    # Assuming standard credentials
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
    req = None
    if data:
        json_data = json.dumps(data).encode()
        req = urllib.request.Request(url, data=json_data, method=method)
        req.add_header("Content-Type", "application/json")
    else:
        req = urllib.request.Request(url, method=method)
    
    req.add_header("Authorization", f"Bearer {TOKEN}")
    
    try:
        with urllib.request.urlopen(req) as response:
             # handle 204 no content
            if response.status == 204:
                return 204, None
            return response.status, json.loads(response.read().decode())
    except urllib.error.HTTPError as e:
        err_msg = e.read().decode()
        print(f"Error {e.code} for {url}: {err_msg}")
        return e.code, json.loads(err_msg) if err_msg else None
    except Exception as e:
        print(f"Error requesting {url}: {e}")
        return 500, None

def verify_duplication():
    print("\n--- Creating Survey with Filters ---")
    
    # 1. Create Survey with Filters
    filtros_test = [{"campo": "departamento", "valor": "Ingeniería Informática"}]
    payload = {
        "nombre": "Encuesta Original (Duplication Test)",
        "descripcion": "Test duplication of filters",
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
                "filtros_json": filtros_test
            }
        ],
        "preguntas": []
    }
    
    status, survey = make_request("/admin/encuestas/", "POST", payload)
    if status != 201:
        print("Failed to create survey")
        return
    
    original_id = survey["id"]
    print(f"Created Original Survey ID: {original_id}")
    
    print("DEBUG: Survey Reponse Rules:", json.dumps(survey.get('reglas', []), indent=2))
    
    # Check if creation saved filters correctly (sanity check)
    if not survey.get('reglas'):
         print("ERROR: No rules found in survey")
         return
         
    first_rule = survey['reglas'][0]
    if 'filtros_json' not in first_rule:
         print(f"ERROR: 'filtros_json' KEY MISSING in rule. Keys found: {list(first_rule.keys())}")
         return

    if first_rule['filtros_json'] != filtros_test:
         print(f"ERROR: Filters verify failed. Expected {filtros_test}, got {first_rule['filtros_json']}")
         return

    print("Original survey has correct filters.")

    # 2. Duplicate Survey
    print(f"\n--- Duplicating Survey {original_id} ---")
    status, copy_survey = make_request(f"/admin/encuestas/{original_id}/duplicar", "POST")
    
    if status != 201:
        print(f"Duplication failed with status {status}")
        return
        
    copy_id = copy_survey["id"]
    print(f"Created Copy Survey ID: {copy_id}")
    
    # 3. Verify Filters in Copy
    copy_filters = copy_survey['reglas'][0]['filtros_json']
    print(f"Copy Filters: {copy_filters}")
    
    if copy_filters == filtros_test:
        print("SUCCESS: Filters were correctly copied!")
    else:
        print("FAILURE: Filters DO NOT MATCH original.")

    # Cleanup
    # make_request(f"/admin/encuestas/{original_id}", "DELETE")
    # make_request(f"/admin/encuestas/{copy_id}", "DELETE")

if __name__ == "__main__":
    if login():
        verify_duplication()
