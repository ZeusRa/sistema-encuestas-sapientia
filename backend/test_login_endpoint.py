import httpx
import asyncio

async def test_login():
    url = "http://127.0.0.1:8000/token" # Assuming standard FastAPI OAuth2 endpoint path or similar
    # Based on main.py check, it might be /login or /token. 
    # Let's check auth.py or main.py. Usually FastAPI uses /token for OAuth2PasswordBearer.
    # Looking at logs/file checks, I haven't seen the auth router path.
    # I'll guess /token, if not I'll try /auth/login.
    
    # Actually, let's look at the previous `test_main.py` or `auth.py` if possible.
    # I can't look now without tool calls. I'll search for it or try both.
    
    params = {
        "username": "admin",
        "password": "admin123"
    }
    
    print(f"Testing login at {url}...")
    try:
        async with httpx.AsyncClient() as client:
            # OAuth2 usually expects form data
            resp = await client.post(url, data=params)
            print(f"Status: {resp.status_code}")
            print(f"Response: {resp.text}")
    except Exception as e:
        print(f"Error connecting: {e}")

if __name__ == "__main__":
    asyncio.run(test_login())
