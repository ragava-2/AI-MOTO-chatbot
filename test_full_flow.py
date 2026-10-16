import os
import sys
from dotenv import load_dotenv

# Ensure standard output can handle utf-8 characters on Windows
sys.stdout.reconfigure(encoding='utf-8')

load_dotenv()

from app import app
from extensions import db
from database.models import User

def test_full_pipeline():
    with app.app_context():
        db.create_all()
        
    client = app.test_client()
    
    # 1. Register/Login test user
    username = "diag_test_user"
    password = "password123"
    email = "diag@test.com"
    
    # Register if not exists
    client.post("/api/register", json={"username": username, "email": email, "password": password})
    
    # Login
    login_res = client.post("/api/login", json={"username": username, "password": password})
    assert login_res.status_code == 200, f"Login failed: {login_res.data}"
    token = login_res.json.get("access_token")
    headers = {"Authorization": f"Bearer {token}"}
    
    print("\n[1] Testing Text Chat Question: 'What is a bike clutch?'")
    chat_res = client.post("/api/chat", data={
        "message": "What is a bike clutch?",
        "language": "English"
    }, headers=headers)
    
    print("Status code:", chat_res.status_code)
    json_data = chat_res.get_json()
    print("Response JSON keys:", list(json_data.keys()) if json_data else None)
    
    assert chat_res.status_code == 200, f"Chat failed: {json_data}"
    assert "response" in json_data, f"'response' key missing in response: {json_data}"
    
    print("\n--- AI RESPONSE ---")
    print(json_data["response"])
    print("-------------------\n")
    
    conv_id = json_data.get("conversation_id")
    
    print("\n[2] Testing Follow-up with Memory in conversation", conv_id)
    followup_res = client.post("/api/chat", data={
        "message": "How do I know if it is worn out?",
        "conversation_id": conv_id,
        "language": "English"
    }, headers=headers)
    assert followup_res.status_code == 200
    print("Followup response preview:", followup_res.get_json()["response"][:200], "...")
    
    print("\n[3] Testing Tamil Language Query: 'பைக் கிளட்ச் என்றால் என்ன?'")
    tamil_res = client.post("/api/chat", data={
        "message": "பைக் கிளட்ச் என்றால் என்ன?",
        "language": "Tamil"
    }, headers=headers)
    assert tamil_res.status_code == 200
    print("Tamil response preview:", tamil_res.get_json()["response"][:200], "...")
    
    print("\n[4] Testing Image Upload Flow (FormData/Multimodal)")
    import io
    from PIL import Image
    
    img = Image.new('RGB', (120, 120), color='blue')
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='JPEG')
    img_byte_arr.seek(0)
    
    img_res = client.post("/api/chat", data={
        "message": "What color is this bike component?",
        "language": "English",
        "file": (img_byte_arr, "test_bike_part.jpg")
    }, headers=headers, content_type="multipart/form-data")
    assert img_res.status_code == 200, f"Image chat failed: {img_res.data}"
    print("Image AI Response:", img_res.get_json()["response"][:200], "...")
    
    print("\n[5] Testing Chat History API")
    convs_res = client.get("/api/conversations", headers=headers)
    assert convs_res.status_code == 200
    conv_list = convs_res.get_json()["conversations"]
    print(f"Total conversations found: {len(conv_list)}")
    assert len(conv_list) >= 1
    
    first_conv_id = conv_list[0]["id"]
    hist_res = client.get(f"/api/conversations/{first_conv_id}", headers=headers)
    assert hist_res.status_code == 200
    print(f"Messages in conversation {first_conv_id}: {len(hist_res.get_json()['history'])}")
    
    print("\n[6] Testing Delete Conversation")
    del_res = client.delete(f"/api/conversations/{first_conv_id}", headers=headers)
    assert del_res.status_code == 200
    print("Delete response:", del_res.get_json())
    
    print("\n==========================================")
    print("ALL API & FEATURE TESTS PASSED SUCCESSFULLY!")
    print("==========================================")

if __name__ == "__main__":
    test_full_pipeline()

