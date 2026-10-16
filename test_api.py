import requests

# 1. Register
res = requests.post("http://127.0.0.1:5000/api/register", json={"username": "testuser", "email": "test@test.com", "password": "password"})
print("Register:", res.status_code, res.text)

# 2. Login
res = requests.post("http://127.0.0.1:5000/api/login", json={"username": "testuser", "password": "password"})
print("Login:", res.status_code, res.text)
token = res.json().get("access_token")

# 3. Chat
res = requests.post("http://127.0.0.1:5000/api/chat", 
    headers={"Authorization": f"Bearer {token}"},
    data={"message": "hi"}
)
print("Chat:", res.status_code, res.text)
