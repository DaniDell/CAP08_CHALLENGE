from fastapi import APIRouter, HTTPException
from retrieval.search import search_google, process_search_results_with_content
from app.config import settings
from app.utils.helpers import save_to_json
import json
from app.services.langchain_service import generate_response_with_citations
from app.utils.knowledge_base import load_knowledge_base, search_in_knowledge_base
import random

router = APIRouter()

# Mensajes predeterminados para cuando no hay citas relevantes
NO_CITATIONS_MESSAGES = [
    "No encontré fuentes externas, pero espero que esta información de mi entrenamiento te sea útil.",
    "Aunque no tengo enlaces externos, confío en que esta información te sea de ayuda.",
    "No encontré referencias externas, pero mi conocimiento puede ser valioso para ti.",
    "No tengo fuentes externas para esta consulta, pero espero que mi respuesta sea útil.",
    "Aunque no hay enlaces disponibles, mi entrenamiento me permite ofrecerte esta información."
]

@router.post("/chat")
def chat_with_bot(query: str):
    """
    Endpoint para interactuar con el chatbot utilizando Langchain.

    :param query: Consulta del usuario.
    :return: Respuesta generada por el chatbot con citas automáticas.
    """
    try:
        # Cargar la base de conocimiento
        knowledge_base = load_knowledge_base()

        # Buscar información relevante en la base de conocimiento
        relevant_data = search_in_knowledge_base(query, knowledge_base)

        # Preparar el contexto para Langchain con limpieza y estructura
        context = "\n".join([
            f"Título: {item['title']}\nDescripción: {item['snippet'].strip()}"
            for item in relevant_data[:5]
        ])

        # Limitar la longitud del contexto si es demasiado largo
        max_context_length = 1500  # Limitar a 1500 caracteres
        if len(context) > max_context_length:
            context = context[:max_context_length] + "..."

        # Generar respuesta con Langchain
        response_with_citations = generate_response_with_citations(context, query, relevant_data)

        # Extraer solo el contenido relevante y limpiar el formato
        if isinstance(response_with_citations, str):
            # Intentar extraer el contenido limpio del campo 'content'
            if "content='" in response_with_citations:
                start_index = response_with_citations.find("content='") + len("content='")
                end_index = response_with_citations.find("'", start_index)
                response_text = response_with_citations[start_index:end_index]
            else:
                response_text = response_with_citations
        else:
            response_text = "No se pudo generar una respuesta válida."

        # Limpiar el formato de la respuesta generada
        response_text = response_text.replace("Respuesta:\n", "").strip()
        response_text = " ".join(response_text.splitlines()).strip()  # Unir líneas en un solo párrafo limpio

        # Agregar enlaces relevantes
        if relevant_data:
            citations = "\n".join([
                f"- {item['title']}: {item['link']}"
                for item in relevant_data[:5]
            ])
        else:
            citations = random.choice(NO_CITATIONS_MESSAGES)

        # Formatear la respuesta final
        final_response = f"{response_text}\n\nEnlaces consultados:\n{citations}"

        return {"text": final_response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al procesar la consulta: {str(e)}")