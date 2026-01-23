import http.client
import json
import urllib.parse
import sys

def reproduce_user_creation():
    conn = http.client.HTTPConnection("localhost", 8000)
    
    try:
        # 1. Login
        print("Authenticating as admin/admin...")
        params = urllib.parse.urlencode({'username': 'admin', 'password': 'admin'})
        headers = {"Content-type": "application/x-www-form-urlencoded", "Accept": "application/json"}
        conn.request("POST", "/token", params, headers)
        response = conn.getresponse()
        data = response.read()
        
        if response.status != 200:
            print(f"Auth Failed: {response.status} - {data.decode()}")
            # Try admin123 just in case
            print("Retrying with admin/admin123...")
            params = urllib.parse.urlencode({'username': 'admin', 'password': 'admin123'})
            conn.request("POST", "/token", params, headers)
            response = conn.getresponse()
            data = response.read()
            if response.status != 200:
                 print(f"Auth Failed again: {response.status} - {data.decode()}")
                 return

        token_data = json.loads(data.decode())
        token = token_data['access_token']
        print("Login Successful.")
        
        auth_header = {"Authorization": f"Bearer {token}", "Content-type": "application/json"}

        # 2. Create Admin User
        user1 = {
            "nombre_usuario": "nuevo_admin_test",
            "clave": "SecurePass123!@",
            "rol": "ADMINISTRADOR"
        }
        print(f"Creating user: {user1['nombre_usuario']} ({user1['rol']})")
        conn.request("POST", "/usuarios/", json.dumps(user1), auth_header)
        r1 = conn.getresponse()
        print(f"Response: {r1.status} - {r1.read().decode()}")

        # 3. Create Directivo User
        user2 = {
            "nombre_usuario": "nuevo_directivo_test",
            "clave": "SecurePass123!@",
            "rol": "DIRECTIVO"
        }
        print(f"Creating user: {user2['nombre_usuario']} ({user2['rol']})")
        conn.request("POST", "/usuarios/", json.dumps(user2), auth_header)
        r2 = conn.getresponse()
        print(f"Response: {r2.status} - {r2.read().decode()}")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    reproduce_user_creation()
