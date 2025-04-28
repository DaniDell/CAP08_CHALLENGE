from dotenv import load_dotenv
import os

# Cargar variables de entorno desde el archivo .env
load_dotenv()

# Variables de entorno
REDIS_URL = os.getenv("REDIS_URL")
HEADER_ACCEPT_ENCODING = os.getenv("HEADER_ACCEPT_ENCODING")
HEADER_USER_AGENT = os.getenv("HEADER_USER_AGENT")
GOOGLE_API_HOST = os.getenv("GOOGLE_API_HOST")
GOOGLE_FIELDS = os.getenv("GOOGLE_FIELDS")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GOOGLE_CX = os.getenv("GOOGLE_CX")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")