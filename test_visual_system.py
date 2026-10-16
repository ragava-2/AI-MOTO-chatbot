import os
import sys
import json

# Ensure utf-8 output on Windows
sys.stdout.reconfigure(encoding='utf-8')

from app import app
from chatbot.image_retriever import match_vehicle_or_component, sanitize_ai_text, enrich_structured_card

def run_tests():
    print("==================================================")
    print("  AI MOTO VISUAL AUTOMOTIVE RETRIEVAL TEST SUITE  ")
    print("==================================================")

    # Test 1: Local Image Files Existence
    print("\n[TEST 1] Verifying Local Image Assets on Disk...")
    base_dir = os.path.dirname(os.path.abspath(__file__))
    comp_dir = os.path.join(base_dir, 'static', 'images', 'components')
    veh_dir = os.path.join(base_dir, 'static', 'images', 'vehicles')
    
    expected_components = [
        'battery.jpg', 'spark_plug.jpg', 'brake_rotor.jpg', 'brake_pad.jpg',
        'brake_caliper.jpg', 'radiator.jpg', 'headlights.jpg', 'rim.jpg',
        'oil_filter.jpg', 'starter.jpg', 'piston.jpg', 'cylinder_head.jpg',
        'clutch_plate.jpg', 'alternator.jpg', 'transmission.jpg', 'fuel_injector.jpg'
    ]
    for comp in expected_components:
        path = os.path.join(comp_dir, comp)
        assert os.path.exists(path), f"Missing component image: {comp}"
    print(f"✓ All {len(expected_components)} automotive component images verified on disk.")

    expected_vehicles = ['bmw_m4_gt3.jpg', 'yamaha_r15.jpg', 'royal_enfield_classic_350.jpg']
    for veh in expected_vehicles:
        path = os.path.join(veh_dir, veh)
        assert os.path.exists(path), f"Missing vehicle image: {veh}"
    print(f"✓ All {len(expected_vehicles)} vehicle showcase images verified on disk.")

    # Test 2: Dynamic Image Matching Engine
    print("\n[TEST 2] Testing Dynamic Image Matching Engine...")
    test_queries = [
        ("My bike battery keeps dying overnight", "component", "battery", "/static/images/components/battery.jpg"),
        ("What causes spark plug misfires?", "component", "spark_plug", "/static/images/components/spark_plug.jpg"),
        ("Tell me about BMW M4 GT3 EVO racing car", "vehicle", "bmw_m4_gt3", "/static/images/vehicles/bmw_m4_gt3.jpg"),
        ("Yamaha R15 specifications and mileage", "vehicle", "yamaha_r15", "/static/images/vehicles/yamaha_r15.jpg"),
        ("Royal Enfield Classic 350 engine sound", "vehicle", "royal_enfield_classic_350", "/static/images/vehicles/royal_enfield_classic_350.jpg"),
        ("என் பைக் கிளட்ச் பிளேட் தேய்ந்துவிட்டது", "component", "clutch_plate", "/static/images/components/clutch_plate.jpg"),
    ]

    for q, exp_type, exp_id, exp_url in test_queries:
        item, match_type = match_vehicle_or_component(q)
        assert item is not None, f"Failed to match query: {q}"
        assert match_type == exp_type, f"Type mismatch for '{q}': got {match_type}, expected {exp_type}"
        assert item['image_url'] == exp_url, f"URL mismatch for '{q}': got {item['image_url']}, expected {exp_url}"
        print(f"  ✓ Query: '{q[:35]}...' -> Matched {match_type.upper()}: {item['name']} ({item['image_url']})")

    # Test 3: Anti-Hallucination Sanitizer
    print("\n[TEST 3] Testing AI Anti-Hallucination Image Protection...")
    hallucinated_output = (
        "Here is your spark plug explanation.\n\n"
        "![Fake Spark Plug](https://external-hallucinated-cdn.com/spark_plug_fake.jpg)\n"
        "Check this alternative image: http://sketchy-auto.net/bad_image.png for reference.\n\n"
        "Always check electrode gap."
    )
    sanitized = sanitize_ai_text(hallucinated_output)
    assert "https://external-hallucinated-cdn.com" not in sanitized
    assert "http://sketchy-auto.net" not in sanitized
    assert "![Fake Spark Plug]" not in sanitized
    assert "Always check electrode gap." in sanitized
    print("✓ Successfully stripped all hallucinated image tags and URLs from AI output.")

    # Test 4: Structured Card Enrichment with Price, Specs & Safety
    print("\n[TEST 4] Testing Structured Card Enrichment...")
    card_input = {
        "response_type": "diagnostic_result",
        "title": "Brake System Inspection",
        "problem_summary": "Squealing noise from front brake"
    }
    enriched = enrich_structured_card(card_input, query_text="Brake pad squealing and worn out", vehicle_type="bike")
    assert enriched.get("image_url") == "/static/images/components/brake_pad.jpg"
    assert enriched.get("is_verified_image") is True
    assert "price_estimate" in enriched
    assert "inr" in enriched["price_estimate"]
    assert "safety_warning" in enriched
    print(f"✓ Enriched Card Image: {enriched.get('image_url')}")
    print(f"✓ Enriched Est. Price: {enriched.get('price_estimate')}")
    print(f"✓ Enriched Safety: {enriched.get('safety_warning')[:70]}...")

    # Test 5: End-to-End Flask API Simulation
    print("\n[TEST 5] Testing End-to-End Chat API Route with Verified Card...")
    with app.test_client() as client:
        # Register a test user
        reg_res = client.post('/api/register', json={
            'username': 'VisualTester',
            'email': 'visualtest@aimoto.com',
            'password': 'Password123!'
        })
        token = None
        if reg_res.status_code == 200:
            token = reg_res.get_json().get('access_token')
        else:
            # Login if already exists
            login_res = client.post('/api/login', json={
                'username': 'VisualTester',
                'password': 'Password123!'
            })
            token = login_res.get_json().get('access_token')

        assert token is not None, "Failed to authenticate test user."
        headers = {'Authorization': f'Bearer {token}'}

        # Send a chat message
        chat_res = client.post('/api/chat', data={
            'message': 'Tell me about the spark plug, its price, and common problems.',
            'vehicle_type': 'bike',
            'language': 'English',
            'mode': 'chat'
        }, headers=headers)

        assert chat_res.status_code == 200, f"Chat API returned {chat_res.status_code}: {chat_res.get_data(as_text=True)}"
        chat_json = chat_res.get_json()
        assert 'structured' in chat_json
        st = chat_json.get('structured')
        assert st is not None, "Structured output should not be None."
        assert 'image_url' in st or any('image_url' in c for c in st.get('components', []))
        print("✓ Chat API successfully returned structured response with verified image and price tags!")
        if st.get('image_url'):
            print(f"  Featured Image: {st.get('image_url')}")
        if st.get('price_estimate'):
            print(f"  Price Estimate: {st.get('price_estimate')}")

    print("\n==================================================")
    print("   ALL 5 VISUAL SYSTEM TESTS PASSED SUCCESSFULLY! ")
    print("==================================================")

if __name__ == '__main__':
    run_tests()
