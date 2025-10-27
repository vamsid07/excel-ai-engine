from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    DEBUG: bool = True
    
    OLLAMA_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.2"
    
    MAX_FILE_SIZE_MB: int = 50
    ALLOWED_EXTENSIONS: str = ".xlsx,.xls"
    
    @property
    def allowed_extensions_list(self) -> List[str]:
        if isinstance(self.ALLOWED_EXTENSIONS, str):
            return [ext.strip() for ext in self.ALLOWED_EXTENSIONS.split(',')]
        return self.ALLOWED_EXTENSIONS
    
    DEFAULT_ROWS: int = 1000
    DEFAULT_STRUCTURED_COLUMNS: int = 10
    DEFAULT_UNSTRUCTURED_COLUMNS: int = 5
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()