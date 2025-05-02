"""
Utilidades de logging para el seguimiento detallado de la aplicación.

Este módulo proporciona funciones para el registro detallado de operaciones
críticas, especialmente enfocado en el seguimiento del procesamiento de conversaciones,
acceso al historial y uso de fuentes externas.
"""

import logging
import os
import json
from datetime import datetime
from typing import Any, Dict, List

# Configurar el logger principal
logger = logging.getLogger(__name__)

# Crear un handler para archivos
def setup_file_logger(log_file="data/app_process.log"):
    """
    Configura un logger que escribe en archivo además de la consola.
    
    Args:
        log_file: Ruta al archivo de log
    """
    # Asegurar que el directorio existe
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    
    # Configurar el formato de los logs
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Configurar el handler de archivo
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setFormatter(file_formatter)
    file_handler.setLevel(logging.DEBUG)
    
    # Añadir el handler al logger raíz
    root_logger = logging.getLogger()
    root_logger.addHandler(file_handler)
    root_logger.setLevel(logging.DEBUG)
    
    # Configurar un archivo separado para prompts completos
    prompt_log_file = "data/prompts_log.log"
    os.makedirs(os.path.dirname(prompt_log_file), exist_ok=True)
    prompt_handler = logging.FileHandler(prompt_log_file, encoding='utf-8')
    prompt_handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
    prompt_handler.setLevel(logging.DEBUG)
    
    # Crear logger específico para prompts
    prompt_logger = logging.getLogger("prompt_logger")
    prompt_logger.addHandler(prompt_handler)
    prompt_logger.setLevel(logging.DEBUG)
    prompt_logger.propagate = False  # Evitar duplicación en el log principal
    
    logger.info(f"Logging configurado en archivo: {log_file}")
    logger.info(f"Logging de prompts configurado en: {prompt_log_file}")

def log_full_prompt(query: str, system_prompt: str, context: str, session_id: str, prompt_type: str):
    """
    Registra el prompt completo enviado al LLM en cada interacción.
    
    Args:
        query: Consulta del usuario
        system_prompt: Prompt del sistema con instrucciones
        context: Contexto adicional de búsqueda web
        session_id: ID de la sesión
        prompt_type: Tipo de prompt utilizado (default, friendly, technical)
    """
    prompt_logger = logging.getLogger("prompt_logger")
    
    # Separador para facilitar la lectura
    separator = "\n" + "="*80 + "\n"
    
    # Formatear el prompt completo
    full_prompt = f"{separator}PROMPT COMPLETO PARA QUERY: '{query}' (SESSION_ID={session_id}, TIPO={prompt_type}){separator}"
    full_prompt += f"SYSTEM PROMPT:\n{system_prompt}\n\n"
    full_prompt += f"USER QUERY:\n{query}\n\n"
    
    if context:
        full_prompt += f"WEB SEARCH CONTEXT:\n{context}\n"
    else:
        full_prompt += "SIN CONTEXTO DE BÚSQUEDA WEB\n"
    
    full_prompt += separator
    
    # Guardar en archivo separado para facilitar la revisión
    prompt_logger.debug(full_prompt)
    
    # Versión resumida para el log principal
    logger.debug(f"Prompt completo para '{query[:30]}...' guardado en prompts_log.log ({len(system_prompt) + len(query) + len(context)} caracteres)")

def log_conversation_history_access(session_id: str, history: List[Dict[str, Any]]):
    """
    Registra el acceso al historial de conversaciones.
    
    Args:
        session_id: ID de sesión
        history: Lista de entradas del historial recuperadas
    """
    logger.debug(f"Accediendo al historial de conversación para session_id={session_id}")
    logger.debug(f"Se recuperaron {len(history)} entradas del historial")
    
    for i, entry in enumerate(history):
        logger.debug(f"Entrada {i+1}:")
        logger.debug(f"  Mensaje del usuario: {entry.get('user_message', '')[:50]}...")
        logger.debug(f"  Fuentes relevantes: {len(entry.get('relevant_sources', []))}")

def log_context_enrichment(has_relevant_info: bool, context_length: int):
    """
    Registra el proceso de enriquecimiento del contexto.
    
    Args:
        has_relevant_info: Si se encontró información relevante
        context_length: Longitud del contexto generado
    """
    if has_relevant_info:
        logger.debug(f"Contexto enriquecido con información relevante: {context_length} caracteres")
    else:
        logger.debug("No se encontró información relevante para enriquecer el contexto")

def log_web_search_results(query: str, results_count: int):
    """
    Registra los resultados de búsqueda web.
    
    Args:
        query: Consulta de búsqueda
        results_count: Número de resultados obtenidos
    """
    logger.debug(f"Búsqueda web para: '{query}'")
    logger.debug(f"Se obtuvieron {results_count} resultados")

def log_conversation_save(user_message: str, session_id: str, has_sources: bool):
    """
    Registra el guardado de una conversación.
    
    Args:
        user_message: Mensaje del usuario
        session_id: ID de sesión
        has_sources: Si se incluyeron fuentes en el guardado
    """
    logger.debug(f"Guardando conversación para session_id={session_id}")
    logger.debug(f"Mensaje del usuario: '{user_message[:50]}...'")
    logger.debug(f"Incluyendo fuentes: {'Sí' if has_sources else 'No'}")