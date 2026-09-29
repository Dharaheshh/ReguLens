from fastapi import FastAPI
from app.config import settings
from app.routers.documents import router as documents_router

app = FastAPI(title="ReguLens API")
app.include_router(documents_router)

@app.get("/api/v1/health")
def health_check():
    return {"status": "ok"}
