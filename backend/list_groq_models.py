import os
import sys
from openai import OpenAI

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

client = OpenAI(
    base_url="https://api.groq.com/openai/v1",
    api_key=os.getenv("LLM_API_KEY")
)

models = client.models.list()
print("Available models:")
for m in models.data:
    print(f" - {m.id}")
