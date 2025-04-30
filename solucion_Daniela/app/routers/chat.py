from fastapi import APIRouter, Query
from app.services.langchain_service import process_query_with_web_search

router = APIRouter()

@router.post("/chat")
async def chat(query: str = Query(..., min_length=1), session_id: str = "default"):
    """
    Endpoint para procesar consultas de chat.
    
    Args:
        query: La consulta del usuario
        session_id: ID de sesión para mantener el contexto
        
    Returns:
        Respuesta generada con fuentes relevantes
    """
    try:
        result = process_query_with_web_search(query, session_id)
        return result
    except Exception as e:
        return {
            "response": f"Error al procesar la consulta: {str(e)}",
            "relevant_sources": []
        }