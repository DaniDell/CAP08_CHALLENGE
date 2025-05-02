"""
Módulo de gestión de la base de conocimientos.

Este módulo proporciona funciones para cargar, procesar y gestionar la base de
conocimientos utilizada por el chatbot. La base de conocimientos está almacenada
en formato JSON y contiene la información que el chatbot utilizará para responder
las consultas de los usuarios.

Funcionalidades principales:
- Carga de datos desde archivo JSON
- Procesamiento y estructuración de la información
- Validación de datos
- Búsqueda de información en Google
"""

import json
import requests
from typing import Dict, List, Any
import logging
import os
import sys

# Añadir el directorio raíz del proyecto al PYTHONPATH
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Importar las funciones de búsqueda
from retrieval.search import search_google, process_search_results

# Configuración del logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuración desde settings
from app.config.settings import settings

def load_knowledge_base(file_path: str = "data/knowledge_base.json") -> Dict[str, Any]:
    """
    Carga la base de conocimientos desde un archivo JSON.
    
    Args:
        file_path (str): Ruta al archivo JSON de la base de conocimientos
        
    Returns:
        Dict[str, Any]: Diccionario con la base de conocimientos cargada
        
    Raises:
        FileNotFoundError: Si no se encuentra el archivo
        json.JSONDecodeError: Si el archivo no es un JSON válido
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
            logger.info(f"Base de conocimientos cargada exitosamente desde {file_path}")
            return data
    except FileNotFoundError:
        logger.error(f"No se encontró el archivo de base de conocimientos en {file_path}")
        raise
    except json.JSONDecodeError as e:
        logger.error(f"Error al decodificar el JSON: {str(e)}")
        raise

def save_knowledge_base(data: Dict[str, Any], file_path: str = "data/knowledge_base.json"):
    """
    Guarda la base de conocimientos en un archivo JSON.
    
    Args:
        data (Dict[str, Any]): Datos de la base de conocimientos a guardar
        file_path (str): Ruta al archivo JSON de la base de conocimientos
        
    Raises:
        Exception: Si ocurre un error al guardar los datos
    """
    try:
        with open(file_path, 'w', encoding='utf-8') as file:
            json.dump(data, file, ensure_ascii=False, indent=4)
            logger.info(f"Base de conocimientos guardada exitosamente en {file_path}")
    except Exception as e:
        logger.error(f"Error al guardar la base de conocimientos: {str(e)}")
        raise

def validate_knowledge_base(data: Dict[str, Any]) -> bool:
    """
    Valida la estructura y contenido de la base de conocimientos.
    
    Args:
        data (Dict[str, Any]): Datos de la base de conocimientos a validar
        
    Returns:
        bool: True si la validación es exitosa, False en caso contrario
    """
    required_fields = ['content', 'metadata']
    
    try:
        # Verificar campos requeridos
        if not all(field in data for field in required_fields):
            logger.error("Faltan campos requeridos en la base de conocimientos")
            return False
            
        # Verificar estructura del contenido
        if not isinstance(data['content'], list):
            logger.error("El campo 'content' debe ser una lista")
            return False
            
        logger.info("Validación de la base de conocimientos exitosa")
        return True
        
    except Exception as e:
        logger.error(f"Error durante la validación: {str(e)}")
        return False

def get_relevant_knowledge(query: str, max_results: int = 5) -> list:
    """
    Obtiene información relevante de la web utilizando la API de Google.
    
    Args:
        query: La consulta del usuario
        max_results: Número máximo de resultados a devolver
        
    Returns:
        Lista de diccionarios con información relevante
    """
    try:
        # Utilizar las funciones del módulo retrieval/search.py
        results = search_google(query, settings.GOOGLE_API_KEY, settings.GOOGLE_CX)
        
        # Procesar los resultados con la función especializada
        processed_results = process_search_results(results)
        
        # Limitar el número de resultados
        return processed_results[:max_results]
    except Exception as e:
        logger.error(f"Error al obtener información relevante: {str(e)}")
        return []