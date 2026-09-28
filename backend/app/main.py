from fastapi import FastAPI
from app.config import settings

app = FastAPI(title="ReguLens API")

@app.get("/api/v1/health")
def health_check():
    return {"status": "ok"}
