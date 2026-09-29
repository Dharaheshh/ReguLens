import os
import sys
import logging
from pydantic import BaseModel

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.llm.provider import call_with_retry_and_fallback, get_provider

logging.basicConfig(level=logging.INFO)

class TestOutput(BaseModel):
    status: str
    message: str

def test_primary():
    print("\n--- Testing Primary Provider (Groq) ---")
    provider = get_provider(use_fallback=False)
    try:
        res = provider.call(
            system_prompt="You are a helpful assistant. Respond with JSON matching the schema.",
            user_content="Say hello.",
            response_model=TestOutput,
            temperature=0.2
        )
        print(f"SUCCESS: {res}")
    except Exception as e:
        print(f"FAILED: {e}")

def test_fallback():
    print("\n--- Testing Fallback Provider (Gemini) ---")
    provider = get_provider(use_fallback=True)
    try:
        res = provider.call(
            system_prompt="You are a helpful assistant. Respond with JSON matching the schema.",
            user_content="Say hello.",
            response_model=TestOutput,
            temperature=0.2
        )
        print(f"SUCCESS: {res}")
    except Exception as e:
        print(f"FAILED: {e}")

if __name__ == "__main__":
    test_primary()
    test_fallback()
