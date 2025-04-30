from dotenv import load_dotenv
import os

# Cargar variables de entorno desde el archivo .env
load_dotenv()

class Settings:
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
    HEADER_ACCEPT_ENCODING = os.getenv("HEADER_ACCEPT_ENCODING")
    HEADER_USER_AGENT = os.getenv("HEADER_USER_AGENT")
    GOOGLE_API_HOST = os.getenv("GOOGLE_API_HOST")
    GOOGLE_FIELDS = os.getenv("GOOGLE_FIELDS")
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
    GOOGLE_CX = os.getenv("GOOGLE_CX")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

settings = Settings()

# Exportar variables para compatibilidad con código existente
# TODO: Refactorizar el código para usar settings.VARIABLE en lugar de importar directamente
globals().update({
    'GOOGLE_API_KEY': settings.GOOGLE_API_KEY,
    'HEADER_ACCEPT_ENCODING': settings.HEADER_ACCEPT_ENCODING,
    'HEADER_USER_AGENT': settings.HEADER_USER_AGENT,
    'GOOGLE_API_HOST': settings.GOOGLE_API_HOST,
    'GOOGLE_FIELDS': settings.GOOGLE_FIELDS,
    'GOOGLE_CX': settings.GOOGLE_CX
})