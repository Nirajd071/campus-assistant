"""
Configuration settings for the NLP engine
"""

import os
from typing import List, Dict, Any
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """Application settings"""
    
    # Server settings
    host: str = "0.0.0.0"
    port: int = int(os.getenv("NLP_ENGINE_PORT", 8001))
    debug: bool = os.getenv("DEBUG", "false").lower() == "true"
    
    # Redis settings
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379")
    
    # Database settings
    database_url: str = os.getenv("DATABASE_URL", "postgresql://localhost/campus_assistant")
    
    # Language settings
    supported_languages: List[str] = ["en", "hi", "bn", "ta", "mr"]
    default_language: str = "en"
    
    # Model settings
    model_cache_dir: str = os.getenv("MODEL_CACHE_DIR", "./models")
    confidence_threshold: float = 0.6
    
    # Session settings
    session_timeout_minutes: int = 30
    max_conversation_turns: int = 10
    
    # Logging
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    
    class Config:
        env_file = ".env"
