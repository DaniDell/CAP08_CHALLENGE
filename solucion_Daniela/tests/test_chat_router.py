"""
Tests para el router de chat.

Este módulo contiene los tests para verificar el funcionamiento
de los endpoints del chat.
"""

from fastapi.testclient import TestClient
import pytest
from unittest.mock import patch, MagicMock

# Importaciones necesarias para las clases base
from langchain_core.messages import BaseMessage
from langchain_core.retrievers import BaseRetriever
from langchain_core.memory import BaseMemory

# Importa tu aplicación FastAPI
from app.main import app

# Inicializa el cliente de prueba
client = TestClient(app)

class MockMessage(BaseMessage):
    content: str = "Test message"
    type: str = "human"

    @property
    def text(self) -> str:
        return self.content

class MockRetriever(BaseRetriever):
    async def _aget_relevant_documents(self, *args, **kwargs):
        return []
    
    def _get_relevant_documents(self, *args, **kwargs):
        return []

class MockMemory(BaseMemory):
    chat_memory: list = []
    memory_variables: list = ["chat_history"]
    
    def load_memory_variables(self, *args, **kwargs):
        return {"chat_history": [MockMessage()]}
        
    def save_context(self, *args, **kwargs):
        pass
        
    def clear(self):
        pass

class MockChain:
    def __init__(self):
        self.response = "Respuesta de prueba"

    def __call__(self, *args, **kwargs):
        return {"answer": self.response}

    def run(self, *args, **kwargs):
        return self.response

def test_root_endpoint():
    """Test del endpoint raíz"""
    response = client.get("/")
    assert response.status_code == 200
    assert "message" in response.json()
    assert "status" in response.json()

@patch('app.services.langchain_service.initialize_chain')
def test_chat_stream_endpoint(mock_init_chain):
    """Test del endpoint de chat en modo streaming"""
    # Configurar el mock de la cadena
    mock_chain = MockChain()
    mock_init_chain.return_value = mock_chain
    
    response = client.post("/api/chat/stream", params={"query": "Hola"})
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")

@patch('app.utils.knowledge_base.load_knowledge_base')
@patch('app.utils.knowledge_base.get_relevant_knowledge')
@patch('app.services.langchain_service.generate_response_with_citations')
def test_chat_endpoint(mock_generate_response, mock_get_relevant, mock_load_kb):
    """Test del endpoint de chat síncrono"""
    # Configurar los mocks
    mock_load_kb.return_value = {"content": []}
    mock_get_relevant.return_value = []
    mock_generate_response.return_value = "Respuesta de prueba"
    
    response = client.post("/api/chat", params={"query": "Hola"})
    assert response.status_code == 200
    assert "response" in response.json()
    assert "relevant_sources" in response.json()

@patch('app.services.langchain_service.initialize_chain')
def test_chat_stream_endpoint_error(mock_init_chain):
    """Test de manejo de errores en el endpoint de streaming"""
    # Probar con una consulta vacía
    response = client.post("/api/chat/stream", params={"query": " "})
    assert response.status_code == 422  # Error de validación