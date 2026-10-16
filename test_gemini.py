import requests
import os
import sys

def test_gemini_key(api_key):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    headers = {'Content-Type': 'application/json'}
    data = {
        "contents": [{
            "parts": [{"text": "Hello! Please reply with a short 'API key is working!' if you receive this."}]
        }]
    }

    print("Testing API key...")
    try:
        response = requests.post(url, headers=headers, json=data)
        if response.status_code == 200:
            result = response.json()
            reply = result['candidates'][0]['content']['parts'][0]['text']
            print("\n✅ SUCCESS! Your API key is working perfectly.")
            print(f"Gemini replied: {reply}")
        else:
            print("\n❌ FAILED. There was an error with your API key.")
            print(f"Status Code: {response.status_code}")
            print(f"Error Details: {response.text}")
    except Exception as e:
        print(f"\n❌ FAILED to connect: {str(e)}")

if __name__ == "__main__":
    key = input("Please paste your Gemini API key here: ").strip()
    if not key:
        print("No API key provided. Exiting.")
        sys.exit(1)
    test_gemini_key(key)
