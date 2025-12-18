from pydantic_settings import BaseSettings
from typing import Optional
import os
from pathlib import Path


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql://opslens:opslens_dev@postgres:5432/opslens"
    
    # Redis
    REDIS_URL: str = "redis://redis:6379/0"
    
    # Environment
    ENVIRONMENT: str = "development"
    
    # Hugging Face
    HUGGINGFACE_API_KEY: Optional[str] = None
    HUGGINGFACE_API_URL: str = "https://api-inference.huggingface.co"
    
    # GitHub
    GITHUB_API_KEY: Optional[str] = None
    GITHUB_ORG: Optional[str] = None
    
    # PagerDuty
    PAGERDUTY_API_KEY: Optional[str] = None
    PAGERDUTY_EMAIL: Optional[str] = None
    
    # Artifacts storage
    ARTIFACTS_DIR: str = "/app/artifacts"
    
    # Model settings
    LLM_MODEL: str = "meta-llama/Llama-3.1-8B-Instruct"
    VLM_MODEL: str = "Qwen/Qwen2-VL-2B-Instruct"
    EMBEDDING_MODEL: str = "BAAI/bge-m3"
    
    class Config:
        env_file = "secrets.env"
        case_sensitive = True


def load_settings() -> Settings:
    """Load settings from environment and secrets file."""
    settings = Settings()
    
    # Try to load from secrets.env if it exists
    secrets_path = Path("/app/secrets.env")
    if secrets_path.exists():
        from dotenv import load_dotenv
        load_dotenv(secrets_path)
        # Reload settings
        settings = Settings()
    
    return settings


settings = load_settings()

