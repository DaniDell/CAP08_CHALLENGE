"""
Punto de entrada principal de la aplicación FastAPI.

Este módulo configura y arranca el servidor FastAPI con los
endpoints y middlewares necesarios.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers.chat_router import router as chat_router
from app.routers.chat import router as chat_basic_router

# Crear la aplicación FastAPI
app = FastAPI(
    title="Servicio de Chat",
    description="API para interactuar con un asistente conversacional",
    version="1.0.0"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir los routers
app.include_router(chat_router)
app.include_router(chat_basic_router)

@app.get("/")
async def root():
    """Endpoint raíz para verificar el estado del servicio."""
    return {
        "message": "Servicio de Chat funcionando correctamente",
        "status": "active"
    }