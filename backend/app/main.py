from fastapi import FastAPI
from app.config import settings
from app.routers.documents import router as documents_router
from app.routers.queries import router as queries_router
from app.routers.responses import router as responses_router

app = FastAPI(title="ReguLens API")
app.include_router(documents_router)
app.include_router(queries_router)
app.include_router(responses_router)

@app.get("/api/v1/health")
def health_check():
    return {"status": "ok"}
