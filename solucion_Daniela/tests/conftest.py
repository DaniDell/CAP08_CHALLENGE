"""
Configuración de pytest y fixtures comunes.

Este módulo contiene la configuración y fixtures compartidos
que se utilizarán en los diferentes archivos de test.
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app
import json

@pytest.fixture
def test_client():
    """
    Fixture que proporciona un cliente de prueba para FastAPI.
    """
    return TestClient(app)

@pytest.fixture
def sample_knowledge_base():
    """
    Fixture que proporciona datos de prueba para la base de conocimientos.
    """
    return {
        "content": [
            {
                "title": "Test Article 1",
                "link": "https://test1.com",
                "text": "This is a test article about Python"
            },
            {
                "title": "Test Article 2",
                "link": "https://test2.com",
                "text": "This is another test article about FastAPI"
            }
        ],
        "metadata": {
            "version": "1.0",
            "created": "2025-04-30"
        }
    }

@pytest.fixture
def mock_openai_response():
    """
    Fixture que proporciona una respuesta simulada de OpenAI.
    """
    return {
        "content": "Esta es una respuesta de prueba del chatbot.",
        "role": "assistant"
    }