"""
Tests para la utilidad de base de conocimientos.

Este módulo contiene los tests para verificar el funcionamiento
de las funciones de gestión de la base de conocimientos.
"""

import pytest
import json
import os
from unittest.mock import patch, mock_open, ANY
from app.utils.knowledge_base import (
    load_knowledge_base,
    save_knowledge_base,
    validate_knowledge_base,
    get_relevant_knowledge
)

TEST_DATA = {
    "content": [
        {
            "title": "Test Article",
            "link": "https://test.com",
            "text": "This is a test article about Python testing"
        }
    ],
    "metadata": {
        "version": "1.0"
    }
}

def test_validate_knowledge_base():
    """Test de validación de la estructura de la base de conocimientos"""
    # Caso válido
    assert validate_knowledge_base(TEST_DATA) == True
    
    # Casos inválidos
    invalid_data = {"content": "not a list"}
    assert validate_knowledge_base(invalid_data) == False
    
    missing_fields = {"wrong_field": []}
    assert validate_knowledge_base(missing_fields) == False

@patch('builtins.open', new_callable=mock_open, read_data=json.dumps(TEST_DATA))
def test_load_knowledge_base(mock_file):
    """Test de carga de la base de conocimientos"""
    # Probar carga desde archivo
    data = load_knowledge_base("fake_path.json")
    assert data == TEST_DATA
    mock_file.assert_called_once_with("fake_path.json", "r", encoding="utf-8")

@patch('builtins.open', new_callable=mock_open)
@patch('redis.StrictRedis')
def test_save_knowledge_base(mock_redis, mock_file):
    """Test de guardado de la base de conocimientos"""
    # Configurar el mock de Redis para simular que no está disponible
    mock_redis.return_value.set.side_effect = Exception("Redis no disponible")
    
    # Guardar los datos
    save_knowledge_base(TEST_DATA, "fake_path.json")
    
    # Verificar que se intentó abrir el archivo
    mock_file.assert_called_once_with("fake_path.json", "w", encoding="utf-8")
    
    # Verificar que se escribió el contenido correcto
    handle = mock_file()
    handle.write.assert_called_with(ANY)  # Usamos ANY porque json.dump escribe en múltiples llamadas
    
    # Reconstruir el JSON escrito y verificar su contenido
    written_calls = handle.write.call_args_list
    written_json = "".join(call[0][0] for call in written_calls)
    assert json.loads(written_json) == TEST_DATA

def test_get_relevant_knowledge():
    """Test de búsqueda de conocimiento relevante"""
    query = "python testing"
    knowledge_base = {
        "content": [
            {
                "title": "Python Testing",
                "link": "https://test.com",
                "text": "This is about Python testing"
            },
            {
                "title": "Other Topic",
                "link": "https://other.com",
                "text": "This is about something else"
            }
        ]
    }
    
    results = get_relevant_knowledge(query, knowledge_base, max_results=1)
    assert len(results) == 1
    assert results[0]["title"] == "Python Testing"
    
    # Probar con una consulta sin resultados
    no_results = get_relevant_knowledge("xyz123", knowledge_base)
    assert len(no_results) == 0