import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    DATABASE_URL: str
    LLM_PROVIDER: str = "groq"
    LLM_BASE_URL: str = "https://api.groq.com/openai/v1"
    LLM_API_KEY: str = ""
    LLM_MODEL: str = "llama-3.3-70b-versatile"
    LLM_TEMPERATURE_DEFAULT: float = 0.2
    
    LLM_FALLBACK_BASE_URL: str = "https://generativelanguage.googleapis.com/v1beta/openai/"
    LLM_FALLBACK_API_KEY: str = ""
    LLM_FALLBACK_MODEL: str = "gemini-2.5-flash-lite"

    EMBEDDING_PROVIDER: str = "local"
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    EMBEDDING_DIMENSION: int = 384
    
    DEMO_BEARER_TOKEN: str = ""
    BACKEND_PORT: int = 8000
    FRONTEND_PORT: int = 5173
    ENVIRONMENT: str = "development"

    # ── Retrieval tuning ──
    # Maximum number of results returned by hybrid_search after fusion/reranking.
    RETRIEVAL_TOP_K: int = 5
    # Minimum normalized RRF fusion score.  Results below this floor are dropped
    # even if they would otherwise be in the top-k.  A requirement can
    # legitimately return fewer than k results, or zero results, when nothing
    # meets the floor — this is correct behaviour, not a bug.
    # NOTE: requires calibration against the real corpus.  A chunk appearing in
    # only one search modality at rank 1 scores 1/(60+1) ≈ 0.0164 — which is
    # a garbage vector-distance-only hit for irrelevant queries.  Setting the
    # floor at 0.02 rejects these while keeping results that appear in both
    # lexical + vector lists (which score ≥ 0.025 even at mediocre ranks).
    RETRIEVAL_MIN_SCORE: float = 0.012
    # Minimum cross-encoder reranker score (Phase 3).  This is on the reranker's
    # own score scale (roughly 0-1), NOT the RRF scale.  Start conservatively.
    RERANK_MIN_SCORE: float = 0.15

    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"), 
        env_file_encoding="utf-8", 
        extra="ignore"
    )

settings = Settings()
