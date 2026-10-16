import os
import sys
import unittest
import json
from PIL import Image
import io
from dotenv import load_dotenv

# Ensure UTF-8 output on Windows
sys.stdout.reconfigure(encoding='utf-8')

load_dotenv(override=True)

from app import app
from extensions import db
from database.models import User
from chatbot.routes import extract_structured_response

class TestAdvancedOutputSuite(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        app.config['TESTING'] = True
        cls.client = app.test_client()
        with app.app_context():
            db.create_all()

        # Register / login test user
        cls.username = "test_adv_user"
        cls.email = "test_adv@example.com"
        cls.password = "AdvPass123!"

        cls.client.post('/api/register', json={
            'username': cls.username,
            'email': cls.email,
            'password': cls.password
        })

        res_login = cls.client.post('/api/login', json={
            'username': cls.username,
            'password': cls.password
        })
        cls.token = res_login.get_json()['access_token']
        cls.headers = {'Authorization': f'Bearer {cls.token}'}

    @classmethod
    def tearDownClass(cls):
        with app.app_context():
            u = User.query.filter_by(username=cls.username).first()
            if u:
                db.session.delete(u)
                db.session.commit()

    def test_01_fallback_and_json_parser_safety(self):
        """Test extract_structured_response with malformed, pure markdown, and valid inputs"""
        print("\n[Test 1] Testing JSON parser and fallback resilience...")
        # Pure markdown
        raw_md = "**Problem Summary**\nThe battery is dead.\n* Cause 1\n* Cause 2"
        text, struct = extract_structured_response(raw_md)
        self.assertEqual(text, raw_md)
        self.assertIsNone(struct)

        # Malformed JSON
        malformed = "Some info <<<STRUCTURED_JSON>>> { 'bad_json': true, <<<END_STRUCTURED_JSON>>> natural summary"
        text2, struct2 = extract_structured_response(malformed)
        self.assertIn("Some info", text2)
        self.assertIsNone(struct2)

        # Valid delimited JSON
        valid = "Overview summary\n<<<STRUCTURED_JSON>>>\n{\"response_type\": \"vehicle_info\", \"title\": \"BMW M4 GT3 EVO\", \"specifications\": [{\"label\": \"Engine\", \"value\": \"3.0L Turbo\"}]}\n<<<END_STRUCTURED_JSON>>>\nMore details."
        text3, struct3 = extract_structured_response(valid)
        self.assertIn("Overview summary", text3)
        self.assertIsNotNone(struct3)
        self.assertEqual(struct3['title'], "BMW M4 GT3 EVO")
        print("  -> Passed all parser safety checks.")

    def test_02_bmw_racing_car_query(self):
        """Test BMW M4 GT3 EVO structured query"""
        print("\n[Test 2] Querying 'Tell me about BMW M4 GT3 EVO'...")
        res = self.client.post('/api/chat', data={
            'message': 'Tell me about BMW M4 GT3 EVO',
            'vehicle_type': 'car',
            'language': 'English'
        }, headers=self.headers)
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIn("response", data)
        print("  -> AI Response length:", len(data["response"]))
        if data.get("structured"):
            print("  -> Structured Card Detected!")
            print("     Title:", data["structured"].get("title"))
            print("     Type:", data["structured"].get("response_type"))
            print("     Specs count:", len(data["structured"].get("specifications", [])))
            print("     Related Qs:", len(data["structured"].get("related_questions", [])))
            self.assertTrue(len(data["structured"].get("specifications", [])) > 0 or len(data["structured"].get("components", [])) > 0)
        else:
            print("  -> Graceful Markdown output returned.")

    def test_03_racing_parts_list_query(self):
        """Test 'What are the parts in a BMW racing car?'"""
        print("\n[Test 3] Querying 'What are the parts in a BMW racing car?'...")
        res = self.client.post('/api/chat', data={
            'message': 'What are the parts in a BMW racing car?',
            'vehicle_type': 'car',
            'language': 'English'
        }, headers=self.headers)
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIn("response", data)
        if data.get("structured"):
            print("  -> Structured Parts Card Detected!")
            print("     Type:", data["structured"].get("response_type"))
            print("     Components:", [c.get("name") for c in data["structured"].get("components", [])[:4]])
        print("  -> Verified parts query response.")

    def test_04_bike_battery_troubleshooting(self):
        """Test 'My bike battery is not working'"""
        print("\n[Test 4] Querying 'My bike battery is not working'...")
        res = self.client.post('/api/chat', data={
            'message': 'My bike battery is not working',
            'vehicle_type': 'bike',
            'language': 'English'
        }, headers=self.headers)
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIn("response", data)
        if data.get("structured"):
            print("  -> Diagnostic Result Card Detected!")
            print("     Safety warning present:", bool(data["structured"].get("safety_warning")))
        print("  -> Verified battery troubleshooting.")

    def test_05_computer_vision_image_upload(self):
        """Test image upload and YOLO detection enrichment"""
        print("\n[Test 5] Testing image upload with multimodal detection...")
        img = Image.new('RGB', (240, 240), color='gray')
        buf = io.BytesIO()
        img.save(buf, format='JPEG')
        buf.seek(0)

        res = self.client.post('/api/chat', data={
            'message': 'Inspect this vehicle component',
            'vehicle_type': 'bike',
            'language': 'English',
            'file': (buf, 'test_component.jpg')
        }, headers=self.headers, content_type='multipart/form-data')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIn("response", data)
        print("  -> Image analysis response received successfully.")

    def test_06_tamil_language_support(self):
        """Test Tamil language query"""
        print("\n[Test 6] Testing Tamil query: 'பைக் பேட்டரி பராமரிப்பு முறைகள் என்ன?'...")
        res = self.client.post('/api/chat', data={
            'message': 'பைக் பேட்டரி பராமரிப்பு முறைகள் என்ன?',
            'vehicle_type': 'bike',
            'language': 'Tamil'
        }, headers=self.headers)
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIn("response", data)
        print("  -> Tamil response length:", len(data["response"]))

if __name__ == "__main__":
    unittest.main()
