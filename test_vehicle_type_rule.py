import sys
import json
sys.stdout.reconfigure(encoding='utf-8')

from chatbot.image_retriever import (
    detect_vehicle_type, detect_brand, validate_image_metadata,
    match_vehicle_or_component, enrich_structured_card
)
from app import app

def test_rule():
    print("================================================================")
    print("  AI MOTO: VEHICLE TYPE VALIDATION & ZERO-CONFUSION RULE TEST   ")
    print("================================================================")

    # 1. Question: "Show me a Yamaha bike image"
    q1 = "Show me a Yamaha bike image"
    print(f"\n[SCENARIO 1] Query: \"{q1}\"")
    v_type_1 = detect_vehicle_type(q1)
    brand_1 = detect_brand(q1)
    print(f"  -> Identified Vehicle Type: {v_type_1}")
    print(f"  -> Identified Brand: {brand_1}")
    assert v_type_1 == "bike", f"Expected bike, got {v_type_1}"
    assert brand_1 == "yamaha", f"Expected yamaha, got {brand_1}"

    matched_1, match_kind_1 = match_vehicle_or_component(q1)
    assert matched_1 is not None, "Should match Yamaha vehicle"
    assert match_kind_1 == "vehicle"
    print(f"  -> Matched Candidate: {matched_1['name']} ({matched_1['image_url']})")

    is_valid_1, reason_1 = validate_image_metadata(matched_1, v_type_1)
    print(f"  -> Image Metadata Validation: {is_valid_1} ({reason_1})")
    assert is_valid_1 is True, "Yamaha R15 is a bike, validation should pass"
    assert matched_1['vehicle_type'] == "bike", "Metadata must be bike, not car"

    enriched_1 = enrich_structured_card(None, query_text=q1, vehicle_type="bike")
    assert enriched_1.get("image_url") == "/static/images/vehicles/yamaha_r15.jpg"
    assert enriched_1.get("is_placeholder", False) is False
    print("  -> Display: Verified relevant Yamaha bike image shown successfully!")

    # 2. Question: "Show me a BMW bike image" (Where catalog only has BMW car)
    q2 = "Show me a BMW bike image"
    print(f"\n[SCENARIO 2] Query: \"{q2}\"")
    v_type_2 = detect_vehicle_type(q2)
    brand_2 = detect_brand(q2)
    print(f"  -> Identified Vehicle Type: {v_type_2}")
    print(f"  -> Identified Brand: {brand_2}")
    assert v_type_2 == "bike"
    assert brand_2 == "bmw"

    enriched_2 = enrich_structured_card(None, query_text=q2, vehicle_type="bike")
    print(f"  -> Image URL Returned: {enriched_2.get('image_url')}")
    print(f"  -> Is Placeholder: {enriched_2.get('is_placeholder')}")
    print(f"  -> Placeholder Title: {enriched_2.get('placeholder_title')}")
    print(f"  -> Placeholder Message: {enriched_2.get('placeholder_message')}")
    
    # CRITICAL CHECK: Must NEVER return BMW car image!
    assert enriched_2.get("image_url") is None, "Car image must NOT be returned for bike query!"
    assert enriched_2.get("is_placeholder") is True, "Placeholder must be activated!"
    assert enriched_2.get("placeholder_type") == "bike", "Placeholder must represent a bike!"
    print("  -> Display: Car image suppressed; Verified Bike Placeholder shown instead!")

    # 3. Question: "Show me a Yamaha car image" (Yamaha is bike, user asks for car)
    q3 = "Show me a Yamaha car image"
    print(f"\n[SCENARIO 3] Query: \"{q3}\"")
    v_type_3 = detect_vehicle_type(q3)
    print(f"  -> Identified Vehicle Type: {v_type_3}")
    assert v_type_3 == "car"

    enriched_3 = enrich_structured_card(None, query_text=q3, vehicle_type="car")
    # CRITICAL CHECK: Must NEVER return Yamaha bike image!
    assert enriched_3.get("image_url") is None, "Bike image must NOT be returned for car query!"
    assert enriched_3.get("is_placeholder") is True
    assert enriched_3.get("placeholder_type") == "car"
    print("  -> Display: Bike image suppressed; Verified Car Placeholder shown instead!")

    # 4. Question: "Show me a BMW car image"
    q4 = "Show me a BMW car image"
    print(f"\n[SCENARIO 4] Query: \"{q4}\"")
    v_type_4 = detect_vehicle_type(q4)
    print(f"  -> Identified Vehicle Type: {v_type_4}")
    assert v_type_4 == "car"

    enriched_4 = enrich_structured_card(None, query_text=q4, vehicle_type="car")
    assert enriched_4.get("image_url") == "/static/images/vehicles/bmw_m4_gt3.jpg"
    assert enriched_4.get("is_placeholder", False) is False
    print("  -> Display: Verified BMW car image shown successfully!")

    # 5. End-to-End Chat API Test with "Show me a Yamaha bike image"
    print("\n[SCENARIO 5] End-to-End Chat API Route with \"Show me a Yamaha bike image\"...")
    with app.test_client() as client:
        login_res = client.post('/api/login', json={
            'username': 'VisualTester',
            'password': 'Password123!'
        })
        if login_res.status_code != 200:
            reg_res = client.post('/api/register', json={
                'username': 'VisualTester',
                'email': 'visual@test.com',
                'password': 'Password123!'
            })
            token = reg_res.get_json().get('access_token')
        else:
            token = login_res.get_json().get('access_token')
        headers = {'Authorization': f'Bearer {token}'}

        chat_res = client.post('/api/chat', data={
            'message': 'Show me a Yamaha bike image',
            'vehicle_type': 'bike',
            'language': 'English'
        }, headers=headers)

        assert chat_res.status_code == 200
        data = chat_res.get_json()
        st = data.get('structured')
        assert st is not None
        assert st.get('image_url') == '/static/images/vehicles/yamaha_r15.jpg'
        assert st.get('vehicle_type') == 'bike'
        assert st.get('is_placeholder') is False
        print(f"  ✓ API structured response confirmed: image_url = {st.get('image_url')}")
        print(f"  ✓ Title = {st.get('title')}, Vehicle Type = {st.get('vehicle_type')}")

    print("\n================================================================")
    print("   ALL VEHICLE TYPE STRICT VALIDATION TESTS PASSED 100%!        ")
    print("================================================================")

if __name__ == '__main__':
    test_rule()
