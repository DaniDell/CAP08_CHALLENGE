"""
Módulo de configuración de la aplicación.

Este módulo gestiona todas las configuraciones y variables de entorno necesarias
para el funcionamiento de la aplicación. Utiliza Pydantic para la validación
de configuraciones y python-dotenv para la carga de variables de entorno.

La configuración incluye:
- Claves de API
- Rutas de archivos
- Configuraciones de CORS
- Otros parámetros del sistema
"""

from functools import lru_cache
from pydantic_settings import BaseSettings
from typing import List, ClassVar
import os
from dotenv import load_dotenv

# Cargar variables de entorno desde el archivo .env
load_dotenv()

class Settings(BaseSettings):
    """
    Clase de configuración principal que define todas las variables de configuración.
    """
    
    # API Keys y configuración de servicios externos
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379")
    
    # Configuración de Google Search
    GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY", "")
    GOOGLE_CX: str = os.getenv("GOOGLE_CX", "")
    GOOGLE_API_HOST: str = os.getenv("GOOGLE_API_HOST", "https://www.googleapis.com/customsearch/v1?")
    GOOGLE_FIELDS: str = os.getenv("GOOGLE_FIELDS", "")
    
    # Headers para peticiones HTTP
    HEADER_ACCEPT_ENCODING: str = os.getenv("HEADER_ACCEPT_ENCODING", "gzip")
    HEADER_USER_AGENT: str = os.getenv("HEADER_USER_AGENT", "")
    
    # Configuración CORS
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:8000",
        "*"
    ]
    
    # Rutas de archivos
    knowledge_base_path: str = "data/knowledge_base.json"
    HISTORICAL_CONVERSATION_FILE: ClassVar[str] = "data/historical_conversation.json"
    
    # Configuración del modelo
    model_name: str = "gpt-3.5-turbo"
    temperature: float = 0.7
    
    class Config:
        """
        Configuración adicional para la clase Settings.
        """
        case_sensitive = True
        env_file = ".env"
        extra = "allow"  # Permitir campos adicionales

@lru_cache()
def get_settings() -> Settings:
    """
    Obtiene una instancia única de la configuración.
    """
    return Settings()

# Crear una instancia de Settings para uso global
settings = get_settings()