"""
Tests para el servicio de LangChain.

Este módulo contiene los tests para verificar el funcionamiento
del servicio de procesamiento de lenguaje natural.
"""

from unittest.mock import patch, MagicMock
from app.services.langchain_service import initialize_chain, process_query, generate_response_with_citations
from langchain_core.memory import BaseMemory
from langchain_core.messages import BaseMessage
from langchain_core.runnables import Runnable
from langchain_core.retrievers import BaseRetriever
from langchain_core.outputs import ChatResult, ChatGenerationChunk
from typing import Any, Optional, List, Dict, AsyncIterator, Iterator, Union

class MockDocument:
    def __init__(self, page_content: str, metadata: dict = None):
        self.page_content = page_content
        self.metadata = metadata or {}

class MockRetriever(BaseRetriever):
    async def _aget_relevant_documents(self, *args, **kwargs):
        return []
    
    def _get_relevant_documents(self, *args, **kwargs):
        return [MockDocument("Test content", {"source": "test"})]

class MockMessage(BaseMessage):
    content: str = "Test message"
    type: str = "human"

    @property
    def text(self) -> str:
        return self.content

class MockMemory(BaseMemory):
    chat_history: list = []
    mem_vars: list = ["chat_history"]
    
    @property
    def memory_variables(self) -> List[str]:
        return self.mem_vars
        
    def load_memory_variables(self, *args, **kwargs):
        return {"chat_history": [MockMessage()]}
        
    def save_context(self, *args, **kwargs):
        pass
        
    def clear(self):
        pass

class MockRunnable(Runnable):
    def invoke(self, input: Any, config: Optional[dict] = None) -> str:
        return "Respuesta de prueba"

    async def ainvoke(self, input: Any, config: Optional[dict] = None) -> str:
        return "Respuesta de prueba"

    def batch(self, inputs: List[Any], config: Optional[dict] = None) -> List[str]:
        return ["Respuesta de prueba" for _ in inputs]

    async def abatch(self, inputs: List[Any], config: Optional[dict] = None) -> List[str]:
        return ["Respuesta de prueba" for _ in inputs]

    def stream(self, input: Any, config: Optional[dict] = None) -> Iterator[str]:
        yield "Respuesta de prueba"

    async def astream(self, input: Any, config: Optional[dict] = None) -> AsyncIterator[str]:
        yield "Respuesta de prueba"

    def transform(self, input: Any) -> str:
        return "Respuesta de prueba"

class MockEmbeddings:
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return [[0.1] * 10 for _ in texts]
        
    def embed_query(self, text: str) -> List[float]:
        return [0.1] * 10

@patch('app.services.langchain_service.ChatOpenAI')
@patch('app.services.langchain_service.FAISS')
@patch('app.services.langchain_service.ConversationBufferMemory')
@patch('app.services.langchain_service.OpenAIEmbeddings')
def test_initialize_chain(mock_embeddings, mock_memory, mock_faiss, mock_chat):
    """Test de inicialización de la cadena de LangChain"""
    # Configurar mocks con implementaciones válidas
    mock_chat.return_value = MockRunnable()
    mock_faiss.load_local.return_value = MockRetriever()
    mock_memory.return_value = MockMemory()
    mock_embeddings.return_value = MockEmbeddings()
    
    chain = initialize_chain()
    assert chain is not None
    assert hasattr(chain, 'invoke')

@patch('app.services.langchain_service.initialize_chain')
@patch('app.services.langchain_service.load_knowledge_base')
def test_process_query(mock_load_kb, mock_init_chain):
    """Test del procesamiento de consultas"""
    # Configurar mocks
    mock_init_chain.return_value = MockRunnable()
    mock_load_kb.return_value = {"content": []}
    
    # Probar el generador
    response = "".join(list(process_query("sopa de calabaza")))
    assert response == "Respuesta de prueba"

@patch('app.services.langchain_service.ChatOpenAI')
def test_generate_response_with_citations(mock_chat):
    """Test de generación de respuestas con citas"""
    # Configurar mock
    mock_chat.return_value = MockRunnable()
    
    context = {"content": []}
    query = "¿Cómo hacer un huevo frito?"
    relevant_data = [
        {
            "title": "Receta de huevo frito",
            "link": "https://ejemplo.com"
        }
    ]
    
    response = generate_response_with_citations(context, query, relevant_data)
    assert isinstance(response, str)
    assert "Respuesta de prueba" in response
    assert "https://ejemplo.com" in response