"""
AURA-EPC Application Settings
Pydantic v2 BaseSettings for environment-driven configuration.
"""
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Groq
    GROQ_API_KEY: str = ""
    GROQ_TEXT_MODEL: str = "llama-3.3-70b-versatile"
    GROQ_VISION_MODEL: str = "qwen3.6-27b"
    GROQ_VISION_FALLBACK_MODEL: str = "meta-llama/llama-4-scout-17b-16e-instruct"

    # Paths
    DATA_DIR: str = "./data"
    MODELS_DIR: str = "./data/models"
    VECTOR_INDEX_PATH: str = "./data/vector_index"

    # Server
    BACKEND_HOST: str = "0.0.0.0"
    BACKEND_PORT: int = 8000
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:3001"

    # Uptime Institute Thresholds (%)
    TIER_I_AVAILABILITY: float = 99.671
    TIER_II_AVAILABILITY: float = 99.741
    TIER_III_AVAILABILITY: float = 99.982
    TIER_IV_AVAILABILITY: float = 99.995


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
