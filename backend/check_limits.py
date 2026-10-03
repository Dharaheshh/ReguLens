import os
import requests

key = os.environ.get("GROQ_API_KEY", "YOUR_API_KEY")
res = requests.post(
    "https://api.groq.com/openai/v1/chat/completions",
    json={"model": "openai/gpt-oss-120b", "messages": [{"role": "user", "content": "hi"}]},
    headers={"Authorization": f"Bearer {key}"}
)

for k, v in res.headers.items():
    print(f"{k}: {v}")
