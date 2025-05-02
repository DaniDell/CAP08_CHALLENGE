"""
Servicio de procesamiento de lenguaje natural utilizando LangChain.

Este módulo proporciona funcionalidades para procesar consultas de usuario utilizando
LangChain, con capacidad de memoria histórica y búsqueda web para enriquecer las respuestas.
"""

from typing import Generator, Dict, Any, List, Optional
from langchain_openai import ChatOpenAI
from langchain.memory import ConversationBufferMemory
from langchain.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory

from app.config.settings import settings
from app.utils.helpers import save_conversation, get_conversation_history
from app.utils.knowledge_base import get_relevant_knowledge
from app.prompts.system_prompt import ASSISTANT_PROMPT, FRIENDLY_ASSISTANT_PROMPT, TECHNICAL_ASSISTANT_PROMPT
import logging

# Configurar logging
logger = logging.getLogger(__name__)

# Diccionario para almacenar la memoria por sesión
session_memories = {}

def create_chain_with_memory(llm, session_id, prompt_type="default"):
    """
    Crea una cadena de procesamiento con memoria histórica.

    Args:
        llm: Modelo de lenguaje configurado.
        session_id: ID de sesión para mantener el historial de la conversación.
        prompt_type: Tipo de prompt a utilizar ("default", "friendly", "technical").

    Returns:
        Una cadena de procesamiento con memoria histórica.
    """
    # Obtener o crear memoria para la sesión
    if session_id not in session_memories:
        session_memories[session_id] = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True
        )

    memory = session_memories[session_id]

    # Seleccionar el prompt según el tipo
    system_prompt = ASSISTANT_PROMPT  # Default
    if prompt_type == "friendly":
        system_prompt = FRIENDLY_ASSISTANT_PROMPT
    elif prompt_type == "technical":
        system_prompt = TECHNICAL_ASSISTANT_PROMPT

    # Crear el prompt con el sistema seleccionado
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "{question}")
    ])

    # Configurar historial de mensajes
    message_history = ChatMessageHistory()
    
    # Cargar historial previo desde el archivo JSON
    prev_history = get_conversation_history(session_id)
    if prev_history:
        # Añadir los mensajes previos al historial
        for entry in prev_history:
            if "user_message" in entry and "assistant_message" in entry:
                message_history.add_user_message(entry["user_message"])
                message_history.add_ai_message(entry["assistant_message"])

    # Envolver la cadena con capacidad de historial
    chain_with_history = RunnableWithMessageHistory(
        {
            "question": lambda x: x["question"] if isinstance(x, dict) else str(x)
        }
        | prompt
        | llm
        | StrOutputParser(),
        lambda _: message_history,
        input_messages_key="question",
        history_messages_key="chat_history"
    )

    return chain_with_history


def initialize_chain(session_id: str, prompt_type: str = "default"):
    """
    Inicializa la cadena de procesamiento de LangChain con memoria histórica.

    Args:
        session_id: ID de sesión para mantener el historial de la conversación.
        prompt_type: Tipo de prompt a utilizar ("default", "friendly", "technical").

    Returns:
        Una cadena de procesamiento con memoria histórica.
    """
    if not settings.OPENAI_API_KEY:
        raise ValueError("No se encontró la API key de OpenAI")

    # Configurar el modelo de lenguaje
    llm = ChatOpenAI(
        api_key=settings.OPENAI_API_KEY,
        model_name=settings.model_name,
        temperature=settings.temperature,
    )

    # Crear la cadena con memoria
    return create_chain_with_memory(llm, session_id, prompt_type)


def process_query(query: str, session_id: str = "default", prompt_type: str = "default") -> Generator[str, None, None]:
    """
    Procesa una consulta del usuario y genera una respuesta en streaming.

    Args:
        query: La consulta del usuario.
        session_id: ID de sesión para mantener el historial de la conversación.
        prompt_type: Tipo de prompt a utilizar ("default", "friendly", "technical").

    Yields:
        Respuesta generada por el modelo.
    """
    try:
        chain = initialize_chain(session_id, prompt_type)
        response = chain.invoke(
            {"question": query},
            config={"configurable": {"session_id": session_id}}
        )
        
        # Guardar la conversación en el historial
        save_conversation(query, response, session_id)
        
        yield response
    except Exception as e:
        logger.error(f"Error al procesar la consulta: {str(e)}")
        yield f"Error al procesar la consulta: {str(e)}"


def process_query_with_web_search(query: str, session_id: str = "default", prompt_type: str = "default") -> Dict[str, Any]:
    """
    Procesa una consulta con memoria y búsqueda web.

    Args:
        query: La consulta del usuario.
        session_id: ID de sesión para mantener el historial de la conversación.
        prompt_type: Tipo de prompt a utilizar ("default", "friendly", "technical").

    Returns:
        Diccionario con la respuesta generada y las fuentes relevantes.
    """
    try:
        # Inicializar la cadena con memoria
        chain = initialize_chain(session_id, prompt_type)
        
        # Realizar búsqueda en Google para obtener información relevante
        relevant_sources = get_relevant_knowledge(query, max_results=5)
        
        # Preparar contexto con la información obtenida
        context = ""
        if relevant_sources:
            context = "Información relevante:\n"
            for idx, result in enumerate(relevant_sources[:3], 1):  # Limitar a 3 resultados para el contexto
                context += f"{idx}. {result['title']}: {result['snippet']}\n"
                context += f"   Fuente: {result['link']}\n\n"

        # Preparar el input como diccionario
        input_dict = {
            "question": str(query),
            "context": context
        }

        # Invocar la cadena asegurando que los tipos sean correctos
        response = chain.invoke(
            input_dict,
            config={"configurable": {"session_id": session_id}}
        )

        # Asegurarse de que la respuesta sea string
        response_text = str(response) if response is not None else ""
        
        # Guardar la conversación en el historial incluyendo las fuentes relevantes
        save_conversation(query, response_text, session_id, relevant_sources)

        return {
            "response": response_text,
            "relevant_sources": relevant_sources
        }
    except Exception as e:
        logger.error(f"Error al procesar la consulta: {str(e)}")
        return {
            "response": f"Error al procesar la consulta: {str(e)}",
            "relevant_sources": []
        }