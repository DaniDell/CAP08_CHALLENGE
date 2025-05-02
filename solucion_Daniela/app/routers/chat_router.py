"""
Router para los endpoints del chat.

Este módulo contiene los endpoints relacionados con
la funcionalidad de chat y procesamiento de consultas.
"""

from fastapi import APIRouter, Query, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse
from app.services.langchain_service import process_query_with_web_search
from app.utils.knowledge_base import load_knowledge_base, get_relevant_knowledge
from typing import List, Dict, Any, Optional
import json
import asyncio
from enum import Enum

router = APIRouter(
    tags=["chat"]
)

class PromptType(str, Enum):
    DEFAULT = "default"
    FRIENDLY = "friendly"
    TECHNICAL = "technical"

@router.post("/api/chat/stream")
async def chat_stream(
    query: str = Query(..., min_length=1), 
    session_id: str = "default",
    prompt_type: PromptType = PromptType.DEFAULT
):
    """
    Endpoint para chat en modo streaming.
    
    Args:
        query: La consulta del usuario
        session_id: ID de sesión para mantener el contexto
        prompt_type: Tipo de prompt a utilizar (default, friendly, technical)
        
    Returns:
        StreamingResponse: Respuesta en streaming con el formato SSE
    """
    if not query.strip():
        raise HTTPException(status_code=422, detail="La consulta no puede estar vacía")
    
    try:
        async def generate():
            # Obtener la respuesta completa
            result = process_query_with_web_search(query, session_id, prompt_type.value)
            
            # Procesar la respuesta principal
            if isinstance(result, dict) and "response" in result:
                response_text = result["response"]
                
                # Dividir la respuesta en párrafos significativos
                paragraphs = [p for p in response_text.split("\n\n") if p.strip()]
                
                # Enviar el contenido principal
                for paragraph in paragraphs:
                    if not paragraph.startswith("Enlaces consultados:"):
                        yield f"data: {json.dumps({'type': 'message', 'content': paragraph.strip()})}\n\n".encode('utf-8')
                        await asyncio.sleep(0.1)
                
                # Enviar solo las fuentes más relevantes si existen
                if "relevant_sources" in result and result["relevant_sources"]:
                    # Filtrar las fuentes para incluir solo las más relevantes
                    sources = filter_most_relevant_sources(query, result["relevant_sources"], response_text)
                    if sources:
                        yield f"data: {json.dumps({'type': 'sources', 'content': sources})}\n\n".encode('utf-8')
            else:
                # Si la respuesta no tiene el formato esperado, enviar como mensaje simple
                yield f"data: {json.dumps({'type': 'message', 'content': str(result)})}\n\n".encode('utf-8')
                
        return StreamingResponse(
            generate(),
            media_type="text/event-stream"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/api/chat")
async def chat(
    query: str = Query(..., min_length=1), 
    session_id: str = "default",
    prompt_type: PromptType = PromptType.DEFAULT
):
    """
    Endpoint para chat síncrono con citas.
    
    Args:
        query: La consulta del usuario
        session_id: ID de sesión para mantener el contexto
        prompt_type: Tipo de prompt a utilizar (default, friendly, technical)
        
    Returns:
        JSONResponse: Respuesta con la información y fuentes relevantes
    """
    if not query.strip():
        raise HTTPException(status_code=422, detail="La consulta no puede estar vacía")
        
    try:
        result = process_query_with_web_search(query, session_id, prompt_type.value)
        
        # Filtrar las fuentes para incluir solo las más relevantes
        if "relevant_sources" in result and result["relevant_sources"]:
            result["relevant_sources"] = filter_most_relevant_sources(
                query, 
                result["relevant_sources"], 
                result.get("response", "")
            )
            
        return JSONResponse(result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def filter_most_relevant_sources(query: str, sources: List[Dict], response: str, max_sources: int = 5) -> List[Dict]:
    """
    Filtra las fuentes para mostrar solo las más relevantes al interés real del usuario.
    
    Args:
        query: La consulta original del usuario
        sources: Lista de fuentes encontradas
        response: La respuesta generada por el modelo
        max_sources: Número máximo de fuentes a devolver
        
    Returns:
        Lista filtrada de fuentes relevantes
    """
    if not sources:
        return []
        
    # Si hay menos fuentes que el máximo, devolver todas
    if len(sources) <= max_sources:
        return sources
        
    # Preparar las palabras clave de la consulta y respuesta para comparación
    query_keywords = set([word.lower() for word in query.split() if len(word) > 3])
    response_keywords = set([word.lower() for word in response.split() if len(word) > 3])
    
    # Calcular puntuación de relevancia para cada fuente
    scored_sources = []
    for source in sources:
        title = source.get("title", "").lower()
        snippet = source.get("snippet", "").lower()
        combined_text = f"{title} {snippet}"
        
        # Puntuación basada en coincidencia con palabras clave de la consulta
        query_score = sum(1 for keyword in query_keywords if keyword in combined_text)
        
        # Puntuación basada en coincidencia con palabras clave de la respuesta
        response_score = sum(1 for keyword in response_keywords if keyword in combined_text)
        
        # Puntuación total - damos más peso a la coincidencia con la consulta
        total_score = (query_score * 2) + response_score
        
        # Añadir a la lista con puntuación
        scored_sources.append((source, total_score))
        
    # Ordenar fuentes por puntuación de relevancia (mayor a menor)
    scored_sources.sort(key=lambda x: x[1], reverse=True)
    
    # Devolver las fuentes más relevantes, hasta el máximo especificado
    return [source for source, _ in scored_sources[:max_sources]]
