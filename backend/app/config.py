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

    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"), 
        env_file_encoding="utf-8", 
        extra="ignore"
    )

settings = Settings()
