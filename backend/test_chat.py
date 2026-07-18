import httpx
import uuid

API_URL = "https://placementor-ai-2qq5.onrender.com/api/v1"

def test():
    email = f"debug_{uuid.uuid4().hex[:8]}@example.com"
    
    # Register
    print("1. Register...")
    r = httpx.post(f"{API_URL}/auth/register", json={
        "email": email, "password": "password123",
        "full_name": "Debug", "role": "student"
    }, timeout=30.0)
    print(f"   Status: {r.status_code}")
    if r.status_code not in (200, 201):
        print(f"   Body: {r.text[:300]}")
        return
    
    # Login
    print("2. Login...")
    r = httpx.post(f"{API_URL}/auth/login", json={
        "email": email, "password": "password123"
    }, timeout=30.0)
    print(f"   Status: {r.status_code}")
    if r.status_code != 200:
        print(f"   Body: {r.text[:300]}")
        return
    token = r.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test /chat/message (non-streaming)
    print("3. POST /chat/message ...")
    r = httpx.post(f"{API_URL}/chat/message", json={
        "message": "hello"
    }, headers=headers, timeout=60.0)
    print(f"   Status: {r.status_code}")
    print(f"   Body: {r.text[:500]}")
    
    # Test /chat/stream
    print("4. POST /chat/stream ...")
    try:
        with httpx.stream("POST", f"{API_URL}/chat/stream", json={
            "message": "hello"
        }, headers=headers, timeout=60.0) as r:
            print(f"   Status: {r.status_code}")
            if r.status_code != 200:
                print(f"   Body: {r.read().decode()[:500]}")
            else:
                for chunk in r.iter_text():
                    print(f"   chunk: {chunk.strip()[:200]}")
    except Exception as e:
        print(f"   Exception: {e}")

if __name__ == "__main__":
    test()
