"""
Configuration settings for the Excel AI Engine
"""
from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # API Settings
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    DEBUG: bool = True
    
    # OpenAI Settings
    OPENAI_API_KEY: str
    OPENAI_MODEL: str = "gpt-4o-mini"
    
    # File Upload Settings
    MAX_FILE_SIZE_MB: int = 50
    ALLOWED_EXTENSIONS: List[str] = [".xlsx", ".xls"]
    
    # Data Generation Settings
    DEFAULT_ROWS: int = 1000
    DEFAULT_STRUCTURED_COLUMNS: int = 10
    DEFAULT_UNSTRUCTURED_COLUMNS: int = 5
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Create a global settings instance
settings = Settings()