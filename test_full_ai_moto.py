import unittest
import os
import io
import json
import base64
from PIL import Image
from dotenv import load_dotenv

# Load env variables
load_dotenv(override=True)

from app import app
from extensions import db
from database.models import User, Conversation, ChatHistory

class TestAIMotoSuite(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        cls.client = app.test_client()
        with app.app_context():
            db.create_all()

    @classmethod
    def tearDownClass(cls):
        with app.app_context():
            db.drop_all()

    def test_01_user_registration(self):
        """Test user registration"""
        res = self.client.post('/api/register', json={
            'username': 'rider_john',
            'email': 'john@example.com',
            'password': 'password123'
        })
        self.assertEqual(res.status_code, 201)
        data = res.get_json()
        self.assertIn("registered successfully", data['message'])

        # Duplicate check
        res_dup = self.client.post('/api/register', json={
            'username': 'rider_john',
            'email': 'john2@example.com',
            'password': 'password123'
        })
        self.assertEqual(res_dup.status_code, 400)

    def test_02_user_login_and_7day_token(self):
        """Test login and 7-day token issuance"""
        res = self.client.post('/api/login', json={
            'username': 'rider_john',
            'password': 'password123'
        })
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIn('access_token', data)
        self.__class__.token = data['access_token']
        self.assertEqual(data['username'], 'rider_john')

    def test_03_domain_restriction_unrelated_query(self):
        """Test that off-topic questions (e.g. Python coding) are rejected politely"""
        headers = {'Authorization': f'Bearer {self.token}'}
        res = self.client.post('/api/chat', data={
            'message': 'How do I write a binary search tree in Python?',
            'vehicle_type': 'bike',
            'language': 'English'
        }, headers=headers)
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIn("AI MOTO", data['response'])
        self.assertTrue("bike" in data['response'].lower() or "vehicle" in data['response'].lower())
        print("\n[TEST 03 Response]:", data['response'])

    def test_04_bike_mechanical_problem_text(self):
        """Test bike mechanical troubleshooting with structured response"""
        headers = {'Authorization': f'Bearer {self.token}'}
        res = self.client.post('/api/chat', data={
            'message': 'My 2023 Yamaha R15 V4 makes a clicking sound when pressing starter and will not start.',
            'vehicle_type': 'bike',
            'language': 'English'
        }, headers=headers)
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.__class__.bike_conv_id = data['conversation_id']
        self.assertEqual(data['vehicle_type'], 'bike')
        self.assertIn("Possible Causes", data['response'])
        print("\n[TEST 04 Bike Response]:", data['response'][:200], "...")

    def test_05_car_mechanical_problem_text(self):
        """Test car mechanical troubleshooting"""
        headers = {'Authorization': f'Bearer {self.token}'}
        res = self.client.post('/api/chat', data={
            'message': 'My Honda City AC is blowing warm air when idling in traffic.',
            'vehicle_type': 'car',
            'language': 'English'
        }, headers=headers)
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.__class__.car_conv_id = data['conversation_id']
        self.assertEqual(data['vehicle_type'], 'car')
        self.assertTrue(len(data['response']) > 50)
        print("\n[TEST 05 Car Response]:", data['response'][:200], "...")

    def test_06_tamil_language_support(self):
        """Test Tamil language assistance"""
        headers = {'Authorization': f'Bearer {self.token}'}
        res = self.client.post('/api/chat', data={
            'message': 'என் பைக் இன்ஜின் அதிகமாக சூடாகிறது. என்ன காரணம்?',
            'vehicle_type': 'bike',
            'language': 'Tamil'
        }, headers=headers)
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(len(data['response']) > 20)
        print("\n[TEST 06 Tamil Response length]:", len(data['response']))

    def test_07_learning_mode(self):
        """Test vehicle learning mode structured explanation"""
        headers = {'Authorization': f'Bearer {self.token}'}
        res = self.client.post('/api/chat', data={
            'message': 'Explain how a motorcycle clutch works.',
            'vehicle_type': 'bike',
            'language': 'English',
            'mode': 'learn'
        }, headers=headers)
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIn("clutch", data['response'].lower())
        print("\n[TEST 07 Learning Mode Response]:", data['response'][:200], "...")

    def test_08_multimodal_image_upload_and_analysis(self):
        """Test image upload and vision analysis"""
        # Create a test 100x100 dummy motorcycle disc brake image
        img = Image.new('RGB', (100, 100), color=(180, 180, 180))
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='PNG')
        img_bytes.seek(0)

        headers = {'Authorization': f'Bearer {self.token}'}
        res = self.client.post('/api/chat', data={
            'message': 'What bike component is this and does it look damaged?',
            'vehicle_type': 'bike',
            'language': 'English',
            'file': (img_bytes, 'test_component.png')
        }, content_type='multipart/form-data', headers=headers)

        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(len(data['response']) > 20)
        print("\n[TEST 08 Vision Response]:", data['response'][:200], "...")

    def test_09_invalid_image_validation(self):
        """Test invalid file extension rejection"""
        fake_file = io.BytesIO(b"Not an image")
        headers = {'Authorization': f'Bearer {self.token}'}
        res = self.client.post('/api/chat', data={
            'message': 'Check this file',
            'vehicle_type': 'bike',
            'file': (fake_file, 'test.pdf')
        }, content_type='multipart/form-data', headers=headers)
        self.assertEqual(res.status_code, 400)
        data = res.get_json()
        self.assertIn("valid JPG, JPEG, PNG, or WEBP", data['message'])

    def test_10_conversation_history_retrieval_and_search(self):
        """Test listing conversations and searching by title/content"""
        headers = {'Authorization': f'Bearer {self.token}'}
        
        # Get all conversations
        res = self.client.get('/api/conversations', headers=headers)
        self.assertEqual(res.status_code, 200)
        convs = res.get_json()['conversations']
        self.assertTrue(len(convs) >= 2)
        
        # Search for 'Honda' or 'Yamaha'
        res_search = self.client.get('/api/conversations?q=Honda', headers=headers)
        self.assertEqual(res_search.status_code, 200)
        search_results = res_search.get_json()['conversations']
        self.assertTrue(any('Honda' in c['title'] for c in search_results))

    def test_11_single_conversation_and_memory_continuation(self):
        """Test loading single conversation messages and continuing chat with context"""
        headers = {'Authorization': f'Bearer {self.token}'}
        conv_id = self.bike_conv_id
        
        # Get conversation
        res = self.client.get(f'/api/conversations/{conv_id}', headers=headers)
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data['conversation']['vehicle_type'], 'bike')
        self.assertTrue(len(data['history']) >= 1)

        # Continue the conversation
        res_continue = self.client.post('/api/chat', data={
            'message': 'I checked the battery terminals and they are tight. What next?',
            'conversation_id': conv_id,
            'vehicle_type': 'bike'
        }, headers=headers)
        self.assertEqual(res_continue.status_code, 200)
        self.assertEqual(res_continue.get_json()['conversation_id'], conv_id)

    def test_12_conversation_deletion(self):
        """Test individual conversation deletion"""
        headers = {'Authorization': f'Bearer {self.token}'}
        conv_id = self.car_conv_id
        
        res = self.client.delete(f'/api/conversations/{conv_id}', headers=headers)
        self.assertEqual(res.status_code, 200)

        # Verify it is gone
        res_check = self.client.get(f'/api/conversations/{conv_id}', headers=headers)
        self.assertEqual(res_check.status_code, 404)

if __name__ == '__main__':
    unittest.main()
