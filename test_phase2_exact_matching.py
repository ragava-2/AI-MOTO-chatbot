"""
Comprehensive Phase 2 Verification Suite
Tests all 10 mandated scenarios for exact model and component matching,
cross-type image prevention, placeholder safeguards, and chat API integration.
"""
import sys
import os
import json

# Ensure AI-chatbot directory is in sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from app import app
from database.models import db, User, Conversation, ChatHistory, VehicleKnowledge
from chatbot.knowledge_matcher import (
    match_exact_vehicle_knowledge,
    detect_vehicle_type,
    match_manufacturer,
    extract_year
)
from chatbot.image_retriever import enrich_structured_card

def run_tests():
    with app.app_context():
        print("=" * 70)
        print("  AI MOTO PHASE 2: EXACT MATCHING & SAFETY TEST SUITE")
        print("=" * 70)

        passed = 0
        total = 10

        # Verify DB is populated
        total_rows = VehicleKnowledge.query.count()
        print(f"\n[INFO] Connected to DB. Total VehicleKnowledge records: {total_rows}")
        assert total_rows >= 20, f"Expected at least 20 records, got {total_rows}"

        # -------------------------------------------------------------
        # Scenario 1: Exact Yamaha YZF-R15 V4 Bike Match
        # -------------------------------------------------------------
        print("\n--- Scenario 1: Exact Yamaha YZF-R15 V4 Bike Match ---")
        q1 = "Show me Yamaha R15 V4 bike image"
        res1 = match_exact_vehicle_knowledge(q1, vehicle_context="bike")
        print(f"Query: '{q1}' -> status={res1.status}, model={res1.model}, confidence={res1.confidence}")
        
        assert res1.matched is True, "Scenario 1 Failed: Expected matched=True"
        assert res1.status == "exact_match", f"Scenario 1 Failed: Expected status='exact_match', got {res1.status}"
        assert res1.vehicle_type == "bike", f"Scenario 1 Failed: Expected vehicle_type='bike', got {res1.vehicle_type}"
        assert res1.manufacturer == "Yamaha", f"Scenario 1 Failed: Expected manufacturer='Yamaha', got {res1.manufacturer}"
        assert res1.image_path is not None and "yamaha_r15" in res1.image_path, "Scenario 1 Failed: Expected verified R15 image path"
        assert res1.confidence in (1.0, 100), f"Scenario 1 Failed: Expected confidence=1.0 or 100, got {res1.confidence}"
        print(">>> Scenario 1 PASSED: Exact bike model matched with verified image & 100% confidence.")
        passed += 1

        # -------------------------------------------------------------
        # Scenario 2: Similar Model Rejection (e.g. Yamaha R3 / R15 V2)
        # -------------------------------------------------------------
        print("\n--- Scenario 2: Similar Model Rejection (Yamaha R3 / R15 V2) ---")
        q2 = "Show me Yamaha R3 bike image"
        res2 = match_exact_vehicle_knowledge(q2, vehicle_context="bike")
        print(f"Query: '{q2}' -> status={res2.status}, matched={res2.matched}, is_placeholder={res2.is_placeholder}")
        
        # Must NOT match R15 V4
        assert res2.status == "unknown_model", f"Scenario 2 Failed: Expected status='unknown_model', got {res2.status}"
        assert res2.is_placeholder is True, "Scenario 2 Failed: Expected placeholder for uncataloged model"
        assert res2.image_path is None, f"Scenario 2 Failed: Expected no image path, got {res2.image_path}"
        
        # Test R15 V2 rejection as well
        q2_v2 = "Show me Yamaha R15 V2 specs"
        res2_v2 = match_exact_vehicle_knowledge(q2_v2, vehicle_context="bike")
        assert res2_v2.status in ("unknown_model", "similar_rejected"), f"Expected rejection of R15 V2, got {res2_v2.status}"
        assert res2_v2.image_path is None
        print(">>> Scenario 2 PASSED: Similar models (R3, R15 V2) strictly rejected without false image substitution.")
        passed += 1

        # -------------------------------------------------------------
        # Scenario 3: Cross-Type Validation (BMW Car vs BMW Bike)
        # -------------------------------------------------------------
        print("\n--- Scenario 3: Cross-Type Validation (BMW Bike vs BMW Car) ---")
        q3_bike = "Show me a BMW bike"
        res3_bike = match_exact_vehicle_knowledge(q3_bike, vehicle_context="bike")
        print(f"Query: '{q3_bike}' (Context: bike) -> status={res3_bike.status}, is_placeholder={res3_bike.is_placeholder}")
        
        # We only have BMW M4 (Car) in catalog, so a BMW bike request MUST NOT return BMW M4 car image
        assert res3_bike.image_path is None, f"Scenario 3 Failed: Car image leaked to bike query! Got: {res3_bike.image_path}"
        assert res3_bike.is_placeholder is True, "Scenario 3 Failed: Expected is_placeholder=True"

        # Now test BMW M4 GT3 with car context
        q3_car = "Show me BMW M4 GT3 EVO"
        res3_car = match_exact_vehicle_knowledge(q3_car, vehicle_context="car")
        print(f"Query: '{q3_car}' (Context: car) -> status={res3_car.status}, model={res3_car.model}, image={res3_car.image_path}")
        assert res3_car.matched is True and res3_car.vehicle_type == "car"
        assert res3_car.image_path is not None and "bmw_m4" in res3_car.image_path
        print(">>> Scenario 3 PASSED: Cross-type validation strictly prevents BMW car from being shown for bike queries.")
        passed += 1

        # -------------------------------------------------------------
        # Scenario 4: Correct Component Matching
        # -------------------------------------------------------------
        print("\n--- Scenario 4: Correct Component Matching (Yamaha R15 Spark Plug) ---")
        q4 = "Yamaha R15 spark plug specifications"
        res4 = match_exact_vehicle_knowledge(q4, vehicle_context="bike")
        print(f"Query: '{q4}' -> status={res4.status}, component={res4.component_name}")
        
        assert res4.matched is True, "Scenario 4 Failed: Expected matched=True"
        assert res4.component_name == "Spark Plug", f"Scenario 4 Failed: Expected 'Spark Plug', got {res4.component_name}"
        assert res4.specifications is not None
        part_num = res4.specifications.get("OEM Part Number", "") or res4.specifications.get("Part Number", "")
        assert "MR8E9" in part_num, f"Scenario 4 Failed: Expected NGK MR8E9 in specs, got {res4.specifications}"
        assert res4.image_path is not None and "spark_plug" in res4.image_path
        print(">>> Scenario 4 PASSED: Component correctly matched with exact verified specs and component image.")
        passed += 1

        # -------------------------------------------------------------
        # Scenario 5: Wrong Component Rejection
        # -------------------------------------------------------------
        print("\n--- Scenario 5: Wrong Component Rejection (Yamaha R15 Turbocharger) ---")
        q5 = "Yamaha R15 turbocharger replacement"
        res5 = match_exact_vehicle_knowledge(q5, vehicle_context="bike")
        print(f"Query: '{q5}' -> status={res5.status}, component={res5.component_name}, is_placeholder={res5.is_placeholder}")
        
        # R15 does not have a cataloged turbocharger
        assert res5.status == "unknown_component", f"Scenario 5 Failed: Expected 'unknown_component', got {res5.status}"
        assert res5.is_placeholder is True, "Scenario 5 Failed: Expected is_placeholder=True"
        assert res5.image_path is None, f"Scenario 5 Failed: Expected image_path=None, got {res5.image_path}"
        assert "not a verified OEM component" in res5.placeholder_message
        print(">>> Scenario 5 PASSED: Non-existent component (turbocharger) not hallucinated or incorrectly mapped.")
        passed += 1

        # -------------------------------------------------------------
        # Scenario 6: Unknown Manufacturer Handling
        # -------------------------------------------------------------
        print("\n--- Scenario 6: Unknown Manufacturer Handling (Ducati Panigale) ---")
        q6 = "Show me Ducati Panigale V4 bike"
        res6 = match_exact_vehicle_knowledge(q6, vehicle_context="bike")
        print(f"Query: '{q6}' -> status={res6.status}, matched={res6.matched}, is_placeholder={res6.is_placeholder}")
        
        assert res6.status == "unknown_manufacturer", f"Scenario 6 Failed: Expected 'unknown_manufacturer', got {res6.status}"
        assert res6.is_placeholder is True
        assert res6.image_path is None
        print(">>> Scenario 6 PASSED: Uncataloged manufacturer triggers safe placeholder.")
        passed += 1

        # -------------------------------------------------------------
        # Scenario 7: Unknown Model Handling
        # -------------------------------------------------------------
        print("\n--- Scenario 7: Unknown Model Handling (Royal Enfield Hunter 350) ---")
        q7 = "Royal Enfield Hunter 350 maintenance"
        res7 = match_exact_vehicle_knowledge(q7, vehicle_context="bike")
        print(f"Query: '{q7}' -> status={res7.status}, matched={res7.matched}, is_placeholder={res7.is_placeholder}")
        
        # Only Classic 350 is cataloged for Royal Enfield
        assert res7.status == "unknown_model", f"Scenario 7 Failed: Expected 'unknown_model', got {res7.status}"
        assert res7.is_placeholder is True
        assert res7.image_path is None
        print(">>> Scenario 7 PASSED: Uncataloged model strictly triggers unknown_model placeholder.")
        passed += 1

        # -------------------------------------------------------------
        # Scenario 8: Missing Verified Image Placeholder
        # -------------------------------------------------------------
        print("\n--- Scenario 8: Missing Verified Image Placeholder (Swift Overview) ---")
        q8 = "Maruti Suzuki Swift car"
        res8 = match_exact_vehicle_knowledge(q8, vehicle_context="car")
        print(f"Query: '{q8}' -> status={res8.status}, model={res8.model}, verified={res8.verified}, is_placeholder={res8.is_placeholder}")
        
        # Swift exists in DB with verified image
        assert res8.matched is True
        assert res8.model == "Swift"
        if res8.image_path is not None:
            assert res8.verified is True
            assert res8.image_path == "/static/images/vehicles/maruti_swift.jpg"
            assert res8.is_placeholder is False
        else:
            assert res8.verified is False
            assert res8.is_placeholder is True
        
        # Check structured card enrichment
        card8 = enrich_structured_card(q8, None, vehicle_context="car")
        assert card8 is not None
        print(">>> Scenario 8 PASSED: Vehicle model image state accurately verified.")
        passed += 1

        # -------------------------------------------------------------
        # Scenario 9: Vehicle Year Mismatch
        # -------------------------------------------------------------
        print("\n--- Scenario 9: Vehicle Year Mismatch (2012 Yamaha R15 V4) ---")
        q9 = "2012 Yamaha R15 V4"
        res9 = match_exact_vehicle_knowledge(q9, vehicle_context="bike")
        print(f"Query: '{q9}' -> status={res9.status}, year_mismatch={res9.year_mismatch}, is_placeholder={res9.is_placeholder}")
        
        assert res9.year_mismatch is True, "Scenario 9 Failed: Expected year_mismatch=True"
        assert res9.status == "year_mismatch", f"Scenario 9 Failed: Expected status='year_mismatch', got {res9.status}"
        assert res9.is_placeholder is True, "Scenario 9 Failed: Expected placeholder due to year mismatch"
        assert res9.image_path is None, f"Scenario 9 Failed: Image should be withheld on year mismatch, got {res9.image_path}"
        print(">>> Scenario 9 PASSED: Out-of-range model year flagged and image withheld with explanation.")
        passed += 1

        # -------------------------------------------------------------
        # Scenario 10: Existing Chat API & Database Integrity
        # -------------------------------------------------------------
        print("\n--- Scenario 10: Existing Chat API & Conversation Integration ---")
        client = app.test_client()

        # Check existing user
        user = User.query.first()
        assert user is not None, "Scenario 10 Failed: No existing user found in DB"
        print(f"Testing with user: {user.username} (ID: {user.id})")

        # Test login to get JWT token
        login_res = client.post("/api/login", json={
            "username": user.username,
            "password": "wrongpassword_test"  # should fail safely
        })
        assert login_res.status_code == 401

        # Generate valid JWT token for existing user
        from flask_jwt_extended import create_access_token
        auth_token = create_access_token(identity=str(user.id))
        headers = {"Authorization": f"Bearer {auth_token}"}

        # Test chat API with authenticated user and form-data
        chat_res = client.post("/api/chat", data={
            "message": "Show me Yamaha R15 V4 bike image",
            "vehicle_type": "bike",
            "language": "English"
        }, headers=headers)
        print(f"Chat API status: {chat_res.status_code}")
        assert chat_res.status_code == 200, f"Scenario 10 Failed: Chat API returned status {chat_res.status_code}"
        
        chat_data = chat_res.get_json()
        assert "response" in chat_data, "Scenario 10 Failed: 'response' key missing from chat output"
        assert "structured" in chat_data, "Scenario 10 Failed: 'structured' key missing from chat output"
        
        struct = chat_data.get("structured")
        assert struct is not None, "Scenario 10 Failed: structured card should not be None for R15 query"
        print(f"Structured Card Title: {struct.get('title')}")
        print(f"Structured Card Image: {struct.get('image_url')}")
        print(f"Structured Card Confidence: {struct.get('confidence')}%")
        print(f"Structured Match Status: {struct.get('match_status')}")
        
        assert "Yamaha" in struct.get("title", ""), "Scenario 10 Failed: Title should contain Yamaha"
        assert struct.get("image_url") is not None and "yamaha_r15" in struct.get("image_url")
        assert struct.get("confidence") == 100
        assert struct.get("match_status") == "exact_match"
        print(">>> Scenario 10 PASSED: Live Chat API enriches response with verified DB data, metadata & confidence.")
        passed += 1

        print("\n" + "=" * 70)
        print(f"  ALL TESTS COMPLETE: {passed}/{total} SCENARIOS PASSED (100% SUCCESS)")
        print("=" * 70)

if __name__ == "__main__":
    run_tests()
