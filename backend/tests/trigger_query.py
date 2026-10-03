import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def run():
    print("Sending POST /api/v1/queries...")
    try:
        res = client.post("/api/v1/queries", json={"query_text": "Is the cultivated meat product microbially safe?"})
        print(f"Status Code: {res.status_code}")
        print(f"Response: {res.json()}")
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    run()
