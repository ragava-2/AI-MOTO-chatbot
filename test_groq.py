import os
import sys
from dotenv import load_dotenv
from groq import Groq

# Ensure standard output can handle utf-8 characters on Windows
sys.stdout.reconfigure(encoding='utf-8')

load_dotenv()

api_key = os.getenv("GROQ_API_KEY")

print(f"API KEY FOUND: {bool(api_key)}")

if not api_key:
    print("ERROR: GROQ_API_KEY not found in .env file")
    sys.exit(1)

client = Groq(api_key=api_key)

try:
    response = client.chat.completions.create(
        model="qwen/qwen3.8-27b",
        messages=[
            {
                "role": "user",
                "content": "What is a motorcycle battery?"
            }
        ],
        max_tokens=500
    )

    print("\nAI RESPONSE:")
    print(response.choices[0].message.content)

except Exception as e:
    print("\n========== GROQ ERROR ==========")
    print("ERROR TYPE:", type(e).__name__)
    print("ERROR MESSAGE:", str(e))
    print("Full Error:", repr(e))
    print("================================")
    raise

