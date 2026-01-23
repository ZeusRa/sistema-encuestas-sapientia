import urllib.request
import urllib.parse
import json
import sys

# Ensure UTF-8 output
sys.stdout.reconfigure(encoding='utf-8')

API_URL = "http://localhost:8000"

def verify():
    # 1. Login
    print("1. Logging in...")
    try:
        data = urllib.parse.urlencode({"username": "admin", "password": "admin123"}).encode()
        req = urllib.request.Request(f"{API_URL}/token", data=data, method="POST")
        with urllib.request.urlopen(req) as response:
            if response.status != 200:
                 print(f"Login Failed: {response.read().decode()}")
                 return
            body = json.loads(response.read().decode())
            token = body["access_token"]
            print("Login Success.")
            
    except Exception as e:
        print(f"Connection/Login Error: {e}")
        return

    headers = {"Authorization": f"Bearer {token}"}

    def fetch(url, headers):
        print(f"DEBUG: Fetching {url}")
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req) as response:
                print(f"DEBUG: Response Status: {response.status}")
                raw = response.read().decode()
                print(f"DEBUG: Raw Content: {raw}")
                return response.status, json.loads(raw)
        except urllib.error.HTTPError as e:
            print(f"DEBUG: HTTPError {e.code}")
            content = e.read().decode()
            print(f"DEBUG: Error Content: {content}")
            try:
                return e.code, json.loads(content)
            except Exception as e:
                return e.code, {"raw": content, "error": str(e)}

    # 2. Fetch Campus
    print("\n2. Fetching Campus...")
    try:
        status, data = fetch(f"{API_URL}/sapientia/campus", headers)
        print(f"Status: {status}")
        print(f"Campus: {data}")
    except Exception as e:
        print(f"Error fetching Campus: {e}")

    # 3. Fetch Facultades
    print("\n3. Fetching Facultades...")
    try:
        status, data = fetch(f"{API_URL}/sapientia/facultades", headers)
        print(f"Facultades (All): {data}")
    except Exception as e:
        print(f"Error fetching Facultades: {e}")

    # 4. Fetch Dashboard IDD
    print("\n4. Fetching Dashboard IDD with filter 'campus=Test'...")
    try:
        # Note: We use campus=Test just to see if it runs (likely returns 0 results as no data matches 'Test')
        status, data = fetch(f"{API_URL}/reportes-avanzados/dashboard/docente/idd?encuesta_id=1&campus=Test", headers)
        print(f"Status: {status}")
        print(f"Data: {data}")
    except Exception as e:
        print(f"Error fetching Dashboard: {e}")

if __name__ == "__main__":
    verify()
