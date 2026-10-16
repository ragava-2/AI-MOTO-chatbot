import os
from dotenv import load_dotenv
import requests

load_dotenv(override=True)

key = os.getenv("OPENAI_API_KEY")

headers = {
    "Authorization": f"Bearer {key}",
    "Content-Type": "application/json"
}
response = requests.get("https://api.groq.com/openai/v1/models", headers=headers)
if response.status_code == 200:
    models = response.json().get("data", [])
    print("Available models:")
    for model in models:
        print(f"- {model['id']}")
else:
    print(f"Error: {response.status_code} - {response.text}")
