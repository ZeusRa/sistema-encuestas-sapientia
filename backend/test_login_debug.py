from fastapi.testclient import TestClient
from main import app
import sys

# Ensure UTF-8 output
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

client = TestClient(app)

def debug_login():
    print("Intentando login vía TestClient...")
    try:
        response = client.post("/token", data={"username": "admin", "password": "admin123"})
        print(f"Status Code: {response.status_code}")
        print(f"Response Body: {response.text}")
    except Exception as e:
        print(f"Excepción capturada: {e}")

if __name__ == "__main__":
    debug_login()
