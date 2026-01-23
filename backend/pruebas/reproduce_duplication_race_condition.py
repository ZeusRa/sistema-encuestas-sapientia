
import threading
import urllib.request
import urllib.parse
import json
import time
import sys

# Configuration
BASE_URL = "http://localhost:8000"
USERNAME = "admin_test"
PASSWORD = "123"

def make_request(method, endpoint, data=None, token=None):
    url = f"{BASE_URL}{endpoint}"
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    
    encoded_data = None
    if data:
        encoded_data = json.dumps(data).encode('utf-8')
    
    if method == "POST" and endpoint == "/token":
        # Form data for token
        encoded_data = urllib.parse.urlencode(data).encode('utf-8')
        headers["Content-Type"] = "application/x-www-form-urlencoded"

    req = urllib.request.Request(url, data=encoded_data, headers=headers, method=method)
    
    try:
        with urllib.request.urlopen(req) as response:
            if response.status >= 200 and response.status < 300:
                body = response.read().decode('utf-8')
                return json.loads(body) if body else {}
            else:
                print(f"Request failed: {response.status}")
                return None
    except urllib.error.HTTPError as e:
        print(f"HTTP Error {e.code}: {e.read().decode('utf-8')}")
        return None
    except Exception as e:
        print(f"Error: {e}")
        return None

def login():
    resp = make_request("POST", "/token", {"username": USERNAME, "password": PASSWORD})
    if resp and "access_token" in resp:
        return resp["access_token"]
    print("Login failed")
    sys.exit(1)

def create_survey(token):
    data = {
        "nombre": f"Test Duplication {int(time.time())}",
        "fecha_inicio": "2025-01-01T00:00:00",
        "fecha_fin": "2025-01-31T23:59:59",
        "prioridad": "opcional",
        "acciones_disparadoras": ["al_iniciar_sesion"],
        "configuracion": {},
        "activo": True,
        "reglas": [{"publico_objetivo": "alumnos"}],
        "preguntas": [
            {"texto_pregunta": "P1", "orden": 1, "tipo": "texto_libre", "opciones": []},
            {"texto_pregunta": "P2", "orden": 2, "tipo": "texto_libre", "opciones": []}
        ]
    }
    resp = make_request("POST", "/admin/encuestas/", data, token)
    if resp:
        return resp["id"]
    sys.exit(1)

def update_survey(token, survey_id, thread_id):
    questions = [
        {"texto_pregunta": f"P1 - Thread {thread_id}", "orden": 1, "tipo": "texto_libre", "opciones": []},
        {"texto_pregunta": f"P2 - Thread {thread_id}", "orden": 2, "tipo": "texto_libre", "opciones": []},
        {"texto_pregunta": f"P3 - Added by {thread_id}", "orden": 3, "tipo": "texto_libre", "opciones": []}
    ]
    
    data = {
        "nombre": f"Test Duplication Updated by {thread_id}",
        "fecha_inicio": "2025-01-01T00:00:00",
        "fecha_fin": "2025-01-31T23:59:59",
        "prioridad": "opcional",
        "acciones_disparadoras": ["al_iniciar_sesion"],
        "configuracion": {},
        "activo": True,
        "reglas": [{"publico_objetivo": "alumnos"}],
        "preguntas": questions
    }
    
    print(f"Thread {thread_id}: Sending update...")
    resp = make_request("PUT", f"/admin/encuestas/{survey_id}", data, token)
    if resp:
        print(f"Thread {thread_id}: Success")
    else:
        print(f"Thread {thread_id}: Failed")

def main():
    print("Starting reproduction script (urllib)...")
    token = login()
    print("Logged in.")
    
    survey_id = create_survey(token)
    print(f"Created survey {survey_id}")
    
    # Run concurrent updates
    t1 = threading.Thread(target=update_survey, args=(token, survey_id, 1))
    t2 = threading.Thread(target=update_survey, args=(token, survey_id, 2))
    
    t1.start()
    t2.start()
    
    t1.join()
    t2.join()
    
    print("Updates finished. Checking results...")
    
    # Check Result
    data = make_request("GET", f"/admin/encuestas/{survey_id}", token=token)
    
    if data:
        print(f"Final Question Count: {len(data['preguntas'])}")
        # Sort by ID to see order of creation
        for p in sorted(data['preguntas'], key=lambda x: x['id']):
            print(f" - ID {p['id']}: {p['texto_pregunta']}")
            
        if len(data['preguntas']) > 3:
            print("FAIL: Duplicates detected!")
        else:
            print("SUCCESS: No duplicates found.")

if __name__ == "__main__":
    main()
