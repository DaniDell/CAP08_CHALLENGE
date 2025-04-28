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

        # Registrar el contexto para depuración
        print("Contexto generado para Langchain:")
        print(context)

        # Generar respuesta con Langchain
        response_with_citations = generate_response_with_citations(context, query, relevant_data)

        # Ajustar el prompt para enfatizar el uso de resultados
        if not relevant_data:
            context += "\nNota: No se encontraron resultados relevantes en la búsqueda externa. Por favor, utiliza únicamente la información proporcionada."

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

@router.get("/test-google-search")
def test_google_search(query: str):
    """
    Endpoint para probar la búsqueda en Google con una query específica.

    :param query: Consulta del usuario.
    :return: Resultados de la búsqueda en Google.
    """
    try:
        from retrieval.search import search_google_with_enhanced_query

        # Realizar la búsqueda en Google con la query mejorada
        results = search_google_with_enhanced_query(query, settings.GOOGLE_API_KEY, settings.GOOGLE_CX)

        # Si no se encuentran resultados, intentar con la query original
        if not results.get("items"):
            print("No se encontraron resultados con la query mejorada. Intentando con la query original...")
            from retrieval.search import search_google
            results = search_google(query, settings.GOOGLE_API_KEY, settings.GOOGLE_CX)

        return {
            "query": query,
            "results": results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al realizar la búsqueda en Google: {str(e)}")

@router.post("/save-search-results")
def save_search_results(query: str):
    """
    Endpoint para guardar los resultados de búsqueda procesados en la base de conocimiento.

    :param query: Consulta del usuario.
    :return: Mensaje de éxito o error.
    """
    try:
        from retrieval.search import search_google, process_search_results

        # Realizar la búsqueda en Google
        results = search_google(query, settings.GOOGLE_API_KEY, settings.GOOGLE_CX)

        # Procesar los resultados de la búsqueda
        processed_results = process_search_results(results)

        # Guardar los resultados procesados en la base de conocimiento
        save_to_json(processed_results)

        return {"message": "Resultados guardados exitosamente."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al guardar los resultados de búsqueda: {str(e)}")

@router.get("/list-knowledge-base")
def list_knowledge_base():
    """
    Endpoint para listar los datos guardados en la base de conocimiento.

    :return: Lista de datos con título, enlace y resumen.
    """
    try:
        from app.utils.knowledge_base import load_knowledge_base  # Importación corregida

        # Cargar la base de conocimiento
        knowledge_base = load_knowledge_base()

        # Formatear los datos para la respuesta
        formatted_data = [
            {
                "title": item.get("title", "Título no disponible"),
                "link": item.get("link", "URL no disponible"),
                "snippet": item.get("snippet", "No se proporcionó un resumen.")
            }
            for item in knowledge_base
        ]

        return {"data": formatted_data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al listar la base de conocimiento: {str(e)}")

@router.post("/integrated-search")
def integrated_search(query: str):
    """
    Endpoint integrado para buscar, procesar, guardar y listar resultados.

    :param query: Consulta del usuario.
    :return: Resultados procesados y guardados en la base de conocimiento.
    """
    try:
        from retrieval.search import search_google, process_search_results
        from app.utils.helpers import save_to_json

        # Realizar la búsqueda en Google
        results = search_google(query, settings.GOOGLE_API_KEY, settings.GOOGLE_CX)

        # Procesar los resultados de la búsqueda
        processed_results = process_search_results(results)

        # Guardar los resultados procesados en la base de conocimiento
        save_to_json(processed_results)

        # Retornar los resultados procesados
        return {"message": "Resultados procesados y guardados exitosamente.", "data": processed_results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en la búsqueda integrada: {str(e)}")