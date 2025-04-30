"""
Router para los endpoints del chat.

Este módulo contiene los endpoints relacionados con
la funcionalidad de chat y procesamiento de consultas.
"""

from fastapi import APIRouter, Query, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse
from app.services.langchain_service import process_query_with_web_search
from app.utils.knowledge_base import load_knowledge_base, get_relevant_knowledge
from typing import List, Dict, Any
import json
import asyncio

router = APIRouter(
    tags=["chat"]
)

@router.post("/api/chat/stream")
async def chat_stream(query: str = Query(..., min_length=1), session_id: str = "default"):
    """
    Endpoint para chat en modo streaming.
    
    Args:
        query: La consulta del usuario
        session_id: ID de sesión para mantener el contexto
        
    Returns:
        StreamingResponse: Respuesta en streaming con el formato SSE
    """
    if not query.strip():
        raise HTTPException(status_code=422, detail="La consulta no puede estar vacía")
    
    try:
        async def generate():
            # Obtener la respuesta completa
            result = process_query_with_web_search(query, session_id)
            
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
                
                # Enviar las fuentes si existen
                if "relevant_sources" in result:
                    sources = result["relevant_sources"]
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
async def chat(query: str = Query(..., min_length=1), session_id: str = "default"):
    """
    Endpoint para chat síncrono con citas.
    
    Args:
        query: La consulta del usuario
        session_id: ID de sesión para mantener el contexto
        
    Returns:
        JSONResponse: Respuesta con la información y fuentes relevantes
    """
    if not query.strip():
        raise HTTPException(status_code=422, detail="La consulta no puede estar vacía")
        
    try:
        result = process_query_with_web_search(query, session_id)
        return JSONResponse(result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
