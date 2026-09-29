import os
import sys
from openai import OpenAI

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

client = OpenAI(
    base_url="https://api.groq.com/openai/v1",
    api_key=os.getenv("LLM_API_KEY")
)

models_to_test = [
    "llama-3.1-70b-versatile",
    "llama-3.1-8b-instant",
    "llama-3.2-90b-text-preview",
    "mixtral-8x7b-32768"
]

for m in models_to_test:
    try:
        print(f"Testing {m}...")
        res = client.chat.completions.create(
            model=m,
            messages=[{"role": "user", "content": "hi"}],
            max_tokens=10
        )
        print(f"  SUCCESS!")
    except Exception as e:
        print(f"  FAILED: {e}")
