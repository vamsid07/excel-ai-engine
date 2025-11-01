import pytest
from app.core.config import Settings, settings


class TestSettings:
    
    def test_default_api_host(self):
        config = Settings()
        assert config.API_HOST == "0.0.0.0"
    
    def test_default_api_port(self):
        config = Settings()
        assert config.API_PORT == 8000
    
    def test_default_debug(self):
        config = Settings()
        assert config.DEBUG is True
    
    def test_default_ollama_url(self):
        config = Settings()
        assert config.OLLAMA_URL == "http://localhost:11434"
    
    def test_default_ollama_model(self):
        config = Settings()
        assert config.OLLAMA_MODEL == "llama3.2"
    
    def test_default_max_file_size(self):
        config = Settings()
        assert config.MAX_FILE_SIZE_MB == 50
    
    def test_default_allowed_extensions(self):
        config = Settings()
        assert config.ALLOWED_EXTENSIONS == ".xlsx,.xls"
    
    def test_allowed_extensions_list(self):
        config = Settings()
        extensions = config.allowed_extensions_list
        
        assert isinstance(extensions, list)
        assert '.xlsx' in extensions
        assert '.xls' in extensions
    
    def test_allowed_extensions_list_strips_whitespace(self):
        config = Settings()
        config.ALLOWED_EXTENSIONS = ".xlsx, .xls, .csv"
        
        extensions = config.allowed_extensions_list
        
        assert all(not ext.startswith(' ') for ext in extensions)
        assert all(not ext.endswith(' ') for ext in extensions)
    
    def test_default_rows(self):
        config = Settings()
        assert config.DEFAULT_ROWS == 1000
    
    def test_default_structured_columns(self):
        config = Settings()
        assert config.DEFAULT_STRUCTURED_COLUMNS == 10
    
    def test_default_unstructured_columns(self):
        config = Settings()
        assert config.DEFAULT_UNSTRUCTURED_COLUMNS == 5
    
    def test_settings_singleton(self):
        assert settings is not None
        assert isinstance(settings, Settings)
    
    def test_custom_api_host(self, monkeypatch):
        monkeypatch.setenv("API_HOST", "127.0.0.1")
        config = Settings()
        assert config.API_HOST == "127.0.0.1"
    
    def test_custom_api_port(self, monkeypatch):
        monkeypatch.setenv("API_PORT", "9000")
        config = Settings()
        assert config.API_PORT == 9000
    
    def test_custom_debug(self, monkeypatch):
        monkeypatch.setenv("DEBUG", "False")
        config = Settings()
        assert config.DEBUG is False
    
    def test_custom_ollama_url(self, monkeypatch):
        monkeypatch.setenv("OLLAMA_URL", "http://custom:11434")
        config = Settings()
        assert config.OLLAMA_URL == "http://custom:11434"
    
    def test_custom_ollama_model(self, monkeypatch):
        monkeypatch.setenv("OLLAMA_MODEL", "llama3")
        config = Settings()
        assert config.OLLAMA_MODEL == "llama3"
    
    def test_custom_max_file_size(self, monkeypatch):
        monkeypatch.setenv("MAX_FILE_SIZE_MB", "100")
        config = Settings()
        assert config.MAX_FILE_SIZE_MB == 100
    
    def test_custom_allowed_extensions(self, monkeypatch):
        monkeypatch.setenv("ALLOWED_EXTENSIONS", ".xlsx,.csv")
        config = Settings()
        assert config.ALLOWED_EXTENSIONS == ".xlsx,.csv"
    
    def test_custom_default_rows(self, monkeypatch):
        monkeypatch.setenv("DEFAULT_ROWS", "500")
        config = Settings()
        assert config.DEFAULT_ROWS == 500
    
    def test_custom_default_structured_columns(self, monkeypatch):
        monkeypatch.setenv("DEFAULT_STRUCTURED_COLUMNS", "15")
        config = Settings()
        assert config.DEFAULT_STRUCTURED_COLUMNS == 15
    
    def test_custom_default_unstructured_columns(self, monkeypatch):
        monkeypatch.setenv("DEFAULT_UNSTRUCTURED_COLUMNS", "8")
        config = Settings()
        assert config.DEFAULT_UNSTRUCTURED_COLUMNS == 8
    
    def test_settings_case_sensitive(self, monkeypatch):
        monkeypatch.setenv("api_host", "lowercase")
        monkeypatch.setenv("API_HOST", "uppercase")
        config = Settings()
        assert config.API_HOST == "uppercase"
    
    def test_allowed_extensions_as_list(self):
        config = Settings()
        config.ALLOWED_EXTENSIONS = [".xlsx", ".xls"]
        
        extensions = config.allowed_extensions_list
        
        assert extensions == [".xlsx", ".xls"]
    
    def test_allowed_extensions_single_value(self):
        config = Settings()
        config.ALLOWED_EXTENSIONS = ".xlsx"
        
        extensions = config.allowed_extensions_list
        
        assert extensions == [".xlsx"]
    
    def test_allowed_extensions_with_spaces(self):
        config = Settings()
        config.ALLOWED_EXTENSIONS = " .xlsx , .xls , .csv "
        
        extensions = config.allowed_extensions_list
        
        assert len(extensions) == 3
        assert '.xlsx' in extensions
        assert '.xls' in extensions
        assert '.csv' in extensions