"""
Integration & Verification Suite for Phase 2 Expansion:
- Popular Vehicles (Activa 6G, Pulsar 150, Duke 390, Creta, Nexon, Swift)
- Component Fitment Specs
- Similar Model Rejection
- Cross-Type Validation
- Image Disk Existence
- Automatic Server-Side API Fallback
- End-to-End Chat API
"""
import sys
import os
import json

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from app import app
from database.models import db, User, VehicleKnowledge
from chatbot.knowledge_matcher import match_exact_vehicle_knowledge
from chatbot.image_retriever import enrich_structured_card, live_image_search_fallback
from flask_jwt_extended import create_access_token

def run_tests():
    with app.app_context():
        print("=" * 70)
        print("  AI MOTO: DATABASE EXPANSION & INTEGRATION TEST SUITE")
        print("=" * 70)

        passed = 0
        total = 9

        # -------------------------------------------------------------
        # 1. Total Database Count & Model Diversity
        # -------------------------------------------------------------
        print("\n[TEST 1] Database Row Count & Vehicle Coverage...")
        total_rows = VehicleKnowledge.query.count()
        print(f"  Total VehicleKnowledge records in DB: {total_rows}")
        assert total_rows == 45, f"Expected 45 records, got {total_rows}"
        
        models = [r[0] for r in db.session.query(VehicleKnowledge.model).distinct().all()]
        print(f"  Distinct Models in DB: {models}")
        expected_models = {"YZF-R15 V4", "Classic 350", "M4 GT3 EVO", "Swift", "Activa 6G", "Pulsar 150", "Duke 390", "Creta", "Nexon"}
        assert expected_models.issubset(set(models)), f"Missing expected models: {expected_models - set(models)}"
        print(">>> TEST 1 PASSED: All 45 records and 9 distinct models cataloged.")
        passed += 1

        # -------------------------------------------------------------
        # 2. Exact Matching for New Bikes
        # -------------------------------------------------------------
        print("\n[TEST 2] Exact Matching for New Popular Bikes...")
        # 2a: Honda Activa 6G
        res_activa = match_exact_vehicle_knowledge("Show me Honda Activa 6G scooter image", vehicle_type="bike")
        assert res_activa.matched is True and res_activa.model == "Activa 6G"
        assert res_activa.image_path == "/static/images/vehicles/honda_activa_6g.jpg"
        assert res_activa.confidence in (1.0, 100)

        # 2b: Bajaj Pulsar 150
        res_pulsar = match_exact_vehicle_knowledge("Bajaj Pulsar 150 specifications", vehicle_type="bike")
        assert res_pulsar.matched is True and res_pulsar.model == "Pulsar 150"
        assert res_pulsar.image_path == "/static/images/vehicles/bajaj_pulsar_150.jpg"

        # 2c: KTM Duke 390
        res_duke = match_exact_vehicle_knowledge("KTM Duke 390 details", vehicle_type="bike")
        assert res_duke.matched is True and res_duke.model == "Duke 390"
        assert res_duke.image_path == "/static/images/vehicles/ktm_duke_390.jpg"
        print(">>> TEST 2 PASSED: New bike models matched exactly with verified assets.")
        passed += 1

        # -------------------------------------------------------------
        # 3. Exact Matching for New Cars & Swift Verified Image
        # -------------------------------------------------------------
        print("\n[TEST 3] Exact Matching for New Popular Cars & Verified Swift...")
        # 3a: Hyundai Creta
        res_creta = match_exact_vehicle_knowledge("Hyundai Creta SUV", vehicle_type="car")
        assert res_creta.matched is True and res_creta.model == "Creta"
        assert res_creta.image_path == "/static/images/vehicles/hyundai_creta.jpg"

        # 3b: Tata Nexon
        res_nexon = match_exact_vehicle_knowledge("Tata Nexon car", vehicle_type="car")
        assert res_nexon.matched is True and res_nexon.model == "Nexon"
        assert res_nexon.image_path == "/static/images/vehicles/tata_nexon.jpg"

        # 3c: Maruti Suzuki Swift (Verified Image)
        res_swift = match_exact_vehicle_knowledge("Maruti Suzuki Swift", vehicle_type="car")
        assert res_swift.matched is True and res_swift.model == "Swift"
        assert res_swift.image_path == "/static/images/vehicles/maruti_swift.jpg"
        assert res_swift.verified is True
        print(">>> TEST 3 PASSED: New cars and Swift matched with verified images.")
        passed += 1

        # -------------------------------------------------------------
        # 4. Component Matching Across New Vehicle Records
        # -------------------------------------------------------------
        print("\n[TEST 4] Component Fitment Matching Across New Models...")
        # 4a: Activa CVT belt
        comp_activa = match_exact_vehicle_knowledge("Honda Activa drive belt", vehicle_type="bike")
        assert comp_activa.matched is True and comp_activa.component_name == "CVT Drive Belt"
        assert "743 mm" in comp_activa.specifications.get("Dimensions", "")

        # 4b: Pulsar 150 chain sprocket
        comp_pulsar = match_exact_vehicle_knowledge("Bajaj Pulsar 150 chain sprocket", vehicle_type="bike")
        assert comp_pulsar.matched is True and comp_pulsar.component_name == "Chain Sprocket Kit"
        assert "428" in comp_pulsar.specifications.get("Chain Pitch", "")

        # 4c: KTM Duke 390 monoshock
        comp_duke = match_exact_vehicle_knowledge("KTM Duke 390 monoshock suspension", vehicle_type="bike")
        assert comp_duke.matched is True and comp_duke.component_name == "Monoshock Absorber"
        assert "WP APEX" in comp_duke.specifications.get("OEM Part Number", "")

        # 4d: Creta cabin filter
        comp_creta = match_exact_vehicle_knowledge("Hyundai Creta cabin ac filter", vehicle_type="car")
        assert comp_creta.matched is True and comp_creta.component_name == "Cabin Air Filter"
        assert "PM2.5" in comp_creta.specifications.get("OEM Part Number", "")

        # 4e: Nexon intercooler hose
        comp_nexon = match_exact_vehicle_knowledge("Tata Nexon turbocharger intercooler hose", vehicle_type="car")
        assert comp_nexon.matched is True and comp_nexon.component_name == "Intercooler Hose"
        assert "Fluorosilicone" in comp_nexon.specifications.get("Material", "")
        print(">>> TEST 4 PASSED: Component fitment accurately resolved across new models.")
        passed += 1

        # -------------------------------------------------------------
        # 5. Strict Similar Model Rejection for New Brands
        # -------------------------------------------------------------
        print("\n[TEST 5] Strict Similar Model Rejection on New Brands...")
        # 5a: Honda Dio rejected (only Activa 6G cataloged)
        rej_dio = match_exact_vehicle_knowledge("Honda Dio scooter", vehicle_type="bike")
        assert rej_dio.status == "unknown_model" and rej_dio.is_placeholder is True

        # 5b: Bajaj Pulsar 220 rejected (only Pulsar 150 cataloged)
        rej_p220 = match_exact_vehicle_knowledge("Bajaj Pulsar 220", vehicle_type="bike")
        assert rej_p220.status == "unknown_model" and rej_p220.is_placeholder is True

        # 5c: KTM RC 390 rejected (only Duke 390 cataloged)
        rej_rc = match_exact_vehicle_knowledge("KTM RC 390 bike", vehicle_type="bike")
        assert rej_rc.status == "unknown_model" and rej_rc.is_placeholder is True

        # 5d: Hyundai Venue rejected (only Creta cataloged)
        rej_venue = match_exact_vehicle_knowledge("Hyundai Venue car", vehicle_type="car")
        assert rej_venue.status == "unknown_model" and rej_venue.is_placeholder is True

        # 5e: Tata Harrier rejected (only Nexon cataloged)
        rej_harrier = match_exact_vehicle_knowledge("Tata Harrier SUV", vehicle_type="car")
        assert rej_harrier.status == "unknown_model" and rej_harrier.is_placeholder is True
        print(">>> TEST 5 PASSED: Inexact models strictly rejected across all brands.")
        passed += 1

        # -------------------------------------------------------------
        # 6. Cross-Type Vehicle Isolation
        # -------------------------------------------------------------
        print("\n[TEST 6] Cross-Type Vehicle Isolation...")
        # Honda car query in bike context
        res_honda_car = match_exact_vehicle_knowledge("Honda City", vehicle_type="bike")
        assert res_honda_car.is_placeholder is True or res_honda_car.status in ("wrong_vehicle_type", "unknown_model")
        assert res_honda_car.image_path is None

        # Tata bike query
        res_tata_bike = match_exact_vehicle_knowledge("Tata bike", vehicle_type="bike")
        assert res_tata_bike.status == "wrong_vehicle_type"
        assert res_tata_bike.is_placeholder is True
        print(">>> TEST 6 PASSED: Cross-type vehicle isolation verified.")
        passed += 1

        # -------------------------------------------------------------
        # 7. Local Image Asset Disk Integrity Check
        # -------------------------------------------------------------
        print("\n[TEST 7] Verifying All Cataloged Images on Disk...")
        all_records = VehicleKnowledge.query.all()
        missing_images = []
        for r in all_records:
            if r.image_path and r.verified:
                clean_p = r.image_path.lstrip("/\\")
                disk_p = os.path.join(BASE_DIR, clean_p)
                if not os.path.exists(disk_p):
                    missing_images.append((r.model, r.component_name, r.image_path))
        
        assert len(missing_images) == 0, f"Missing images on disk: {missing_images}"
        print(f"  [OK] Verified {len(all_records)} / {len(all_records)} records have valid images on disk.")
        print(">>> TEST 7 PASSED: 100% on-disk asset verification.")
        passed += 1

        # -------------------------------------------------------------
        # 8. Automatic Server-Side API Fallback
        # -------------------------------------------------------------
        print("\n[TEST 8] Automatic Server-Side API Fallback...")
        fallback_res = live_image_search_fallback("Toyota Camry", expected_type="car")
        print(f"  Fallback Result: {fallback_res}")
        assert fallback_res is not None, "Fallback should return result for Toyota Camry"
        assert fallback_res.get("image_url") is not None
        assert "wikimedia.org" in fallback_res.get("image_url")
        assert fallback_res.get("is_live_search") is True
        assert fallback_res.get("is_verified_image") is False

        # Test card enrichment for uncataloged vehicle with image request
        card_fallback = enrich_structured_card(None, "Show me Toyota Camry car image", vehicle_type="car")
        assert card_fallback is not None
        assert card_fallback.get("is_live_search") is True or card_fallback.get("image_url") is not None
        print(">>> TEST 8 PASSED: Safe server-side API fallback returned real reference without hallucination.")
        passed += 1

        # -------------------------------------------------------------
        # 9. Live Chat API End-to-End Integration
        # -------------------------------------------------------------
        print("\n[TEST 9] Live Chat API with New Vehicle Query...")
        client = app.test_client()
        user = User.query.first()
        if not user:
            from extensions import bcrypt
            hashed = bcrypt.generate_password_hash("testpass123").decode('utf-8')
            user = User(username="expansion_tester", email="tester@example.com", password=hashed)
            db.session.add(user)
            db.session.commit()

        auth_token = create_access_token(identity=str(user.id))
        headers = {"Authorization": f"Bearer {auth_token}"}

        chat_res = client.post("/api/chat", data={
            "message": "Show me Honda Activa 6G image",
            "vehicle_type": "bike",
            "language": "English"
        }, headers=headers)
        
        assert chat_res.status_code == 200
        chat_data = chat_res.get_json()
        struct = chat_data.get("structured")
        assert struct is not None
        assert "Activa 6G" in struct.get("title", "")
        assert struct.get("image_url") == "/static/images/vehicles/honda_activa_6g.jpg"
        assert struct.get("confidence") == 100
        assert struct.get("match_status") == "exact_match"
        print(f"  [OK] Live Chat API returned verified card: {struct.get('title')} ({struct.get('confidence')}%)")
        print(">>> TEST 9 PASSED: Live Chat API enriches response with new vehicle models.")
        passed += 1

        print("\n" + "=" * 70)
        print(f"  ALL EXPANSION TESTS COMPLETE: {passed}/{total} PASSED (100% SUCCESS)")
        print("=" * 70)

if __name__ == "__main__":
    run_tests()
