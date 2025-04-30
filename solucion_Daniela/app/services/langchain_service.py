"""
Servicio de procesamiento de lenguaje natural utilizando LangChain.

Este módulo implementa la lógica de procesamiento de consultas utilizando el framework LangChain.
Proporciona funcionalidades para:
- Inicialización y gestión de la cadena de procesamiento
- Manejo de consultas en modo streaming
- Generación de respuestas con citas
"""

from pathlib import Path
from typing import Generator, Dict, Any, List, Optional
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain.memory import ConversationBufferMemory
from langchain_community.vectorstores import FAISS
from langchain.prompts import PromptTemplate, ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough, RunnableLambda
from langchain_core.output_parsers import StrOutputParser
from langchain_core.messages import HumanMessage, AIMessage
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.callbacks import CallbackManagerForRetrieverRun

from app.utils.knowledge_base import load_knowledge_base
from app.config.settings import settings
from app.utils.knowledge_base import get_relevant_knowledge as kb_get_relevant_knowledge

import requests
import json

def create_history_aware_retriever(llm, retriever, memory):
    """
    Crea un retriever que tiene en cuenta el historial de conversación.
    """
    REPHRASE_TEMPLATE = """Dada la siguiente conversación y una pregunta, reformula la pregunta 
    para obtener la información más relevante del contexto.

    Chat History:
    {chat_history}
    
    Pregunta: {question}
    
    Pregunta Reformulada:"""
    
    condense_question_prompt = PromptTemplate.from_template(REPHRASE_TEMPLATE)
    
    def format_chat_history(chat_history):
        return "\n".join(
            f"{msg.type.title()}: {msg.content}" for msg in chat_history
        )

    def get_chat_history():
        memory_vars = memory.load_memory_variables({})
        return memory_vars.get("chat_history", [])

    # Pipeline para reformular la pregunta
    condense_question_chain = (
        {"chat_history": lambda x: format_chat_history(get_chat_history()), "question": RunnablePassthrough()}
        | condense_question_prompt
        | llm
        | StrOutputParser()
    )

    # Pipeline para la búsqueda usando el nuevo método invoke
    conversational_retrieval_chain = RunnableLambda(
        lambda x: retriever.invoke(condense_question_chain.invoke(x))
    )

    return conversational_retrieval_chain

def create_retrieval_chain(llm, context_retriever):
    """
    Crea una cadena de procesamiento que combina el contexto recuperado con la pregunta.
    """
    prompt = ChatPromptTemplate.from_messages([
        ("system", """Eres un asistente conversacional que proporciona respuestas concisas y directas.

        Directrices:
        1. Mantén tus respuestas breves y al punto
        2. Usa lenguaje claro y sencillo
        3. Estructura tu respuesta en máximo 2-3 párrafos cortos
        4. Comparte solo los enlaces más relevantes que el usuario pueda consultar para profundizar en el tema
        
        Recuerda: La brevedad y claridad son esenciales. No necesitas explicar todo - proporciona la información más importante
        y deja que el usuario decida si quiere investigar más a través de los enlaces proporcionados."""),
        ("human", "{question}"),
        ("human", "Contexto encontrado:\n{context}")
    ])

    def format_docs(docs):
        return "\n\n".join(doc.page_content for doc in docs)

    # Pipeline completo
    chain = (
        {
            "context": context_retriever | format_docs,
            "question": RunnablePassthrough()
        }
        | prompt
        | llm
        | StrOutputParser()
    )

    return chain

def initialize_chain():
    """
    Inicializa la cadena de procesamiento de LangChain.
    """
    if not settings.OPENAI_API_KEY:
        raise ValueError("No se encontró la API key de OpenAI")
    
    
        
    # Solo configuramos los parámetros esenciales
    llm = ChatOpenAI(
        api_key=settings.OPENAI_API_KEY,
        model_name=settings.model_name,
        temperature=settings.temperature,
    )
    
    embeddings = OpenAIEmbeddings(
        api_key=settings.OPENAI_API_KEY,
    )
    
    # Asegurarse de que existe el directorio para el índice FAISS
    index_dir = Path(settings.faiss_index_path).parent
    index_dir.mkdir(parents=True, exist_ok=True)
    
    # Intentar cargar el índice existente o crear uno nuevo
    try:
        vectorstore = FAISS.load_local(
            settings.faiss_index_path,
            embeddings,
            allow_dangerous_deserialization=True
        )
        # Convertir el vectorstore en un retriever
        retriever = vectorstore.as_retriever()
    except Exception as e:
        # Si no existe el índice, creamos uno nuevo
        knowledge_base = load_knowledge_base()
        texts = []
        if isinstance(knowledge_base, list):
            texts = [doc.get("text", "") for doc in knowledge_base]
        elif isinstance(knowledge_base, dict):
            texts = [doc.get("text", "") for doc in knowledge_base.get("content", [])]
            
        if not texts:
            texts = ["Información inicial"]  # Texto placeholder si no hay contenido
            
        vectorstore = FAISS.from_texts(texts, embeddings)
        vectorstore.save_local(settings.faiss_index_path)
        # Convertir el vectorstore en un retriever
        retriever = vectorstore.as_retriever()

    # Configuración de la memoria con los nuevos parámetros recomendados
    memory = ConversationBufferMemory(
        memory_key="chat_history",
        return_messages=True,
        output_key="output"  # Añadido para evitar la advertencia de depreciación
    )

    # Crear el retriever consciente del historial
    history_aware_retriever = create_history_aware_retriever(llm, retriever, memory)
    
    # Crear la cadena completa
    chain = create_retrieval_chain(llm, history_aware_retriever)
    
    # Envolver la cadena con la memoria
    message_history = ChatMessageHistory()
    chain_with_history = RunnableWithMessageHistory(
        chain,
        lambda session_id: message_history,
        input_messages_key="question",
        history_messages_key="chat_history"
    )
    
    return chain_with_history

def get_relevant_knowledge(query: str) -> List[Dict[str, Any]]:
    """
    Obtiene información relevante de la web para una consulta dada.
    """
    try:
        # Usar la implementación de knowledge_base.py
        return kb_get_relevant_knowledge(query)
    except Exception as e:
        print(f"Error en búsqueda web: {str(e)}")
        return []

def process_query(query: str, session_id: str = "default") -> Generator[str, None, None]:
    """
    Procesa una consulta del usuario y genera una respuesta en streaming.
    """
    try:
        chain = initialize_chain()
        response = chain.invoke(
            {"question": query},
            config={"configurable": {"session_id": session_id}}
        )
        yield response
    except Exception as e:
        yield f"Error al procesar la consulta: {str(e)}"

def process_query_with_web_search(query: str, session_id: str = "default") -> Dict[str, Any]:
    """
    Procesa una consulta con memoria y búsqueda web.
    """
    try:
        # Inicializar la cadena con memoria
        chain = initialize_chain()
        
        # Obtener información relevante de la web
        relevant_data = get_relevant_knowledge(query)
        
        # Preparar el contexto enriquecido
        web_context = "\n\n".join([
            f"Fuente: {item['title']}\n"
            f"Información: {item['snippet']}\n"
            f"URL: {item['link']}"
            for item in relevant_data[:5]
        ])
        
        # Invocar la cadena con memoria y contexto enriquecido
        enhanced_query = {
            "question": f"{query}\n\nContexto adicional de la web:\n{web_context}"
        }
        
        response = chain.invoke(
            enhanced_query,
            config={"configurable": {"session_id": session_id}}
        )
        
        # Formatear las citas
        citations = "\n".join([
            f"- {item['title']}: {item['link']}"
            for item in relevant_data[:5]
        ])
        
        return {
            "response": f"{response}\n\nEnlaces consultados:\n{citations}",
            "relevant_sources": relevant_data
        }
    except Exception as e:
        return {
            "response": f"Error al procesar la consulta: {str(e)}",
            "relevant_sources": []
        }

def generate_response_with_citations(context: Dict[str, Any], query: str) -> Dict[str, Any]:
    """
    Genera una respuesta utilizando Langchain y agrega citas automáticas.
    """
    try:
        # Obtener información relevante de la web
        relevant_data = get_relevant_knowledge(query)
        
        llm = ChatOpenAI(
            api_key=settings.OPENAI_API_KEY,
            model_name=settings.model_name,
            temperature=settings.temperature,
        )
        
        # Enriquecer el contexto con la información de la web
        web_context = "\n\n".join([
            f"Título: {item['title']}\nDescripción: {item['snippet']}\nFuente: {item['displayLink']}"
            for item in relevant_data[:3]  # Usar solo los 3 primeros resultados para el contexto
        ])
        
        enriched_context = f"{context}\n\nInformación adicional de la web:\n{web_context}"
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """Eres un asistente conversacional experto en responder preguntas.
            Usa la información proporcionada en el contexto y la información adicional de la web.
            Incluye referencias a las fuentes cuando sea apropiado."""),
            ("human", "{query}"),
            ("human", "Contexto: {context}")
        ])

        chain = prompt | llm | StrOutputParser()
        response = chain.invoke({"context": enriched_context, "query": query})

        # Formatear las citas
        citations = "\n".join([
            f"- {item['title']}: {item['link']}"
            for item in relevant_data[:5]
        ])

        return {
            "response": f"{response}\n\nEnlaces consultados:\n{citations}",
            "relevant_sources": relevant_data
        }
    except Exception as e:
        return {
            "response": f"Error al generar la respuesta: {str(e)}",
            "relevant_sources": []
        }

# URL base de la API
BASE_URL = "http://localhost:8000"

def chat_request(query):
    """Realiza una solicitud al endpoint de chat."""
    response = requests.post(f"{BASE_URL}/api/chat", params={"query": query})
    return response.json()

def main():
    print("=== Cliente de Chat en Consola ===")
    print("Escribe 'salir' para terminar.")
    
    while True:
        query = input("\nTú: ")
        if query.lower() in ["salir", "exit", "quit"]:
            break
            
        try:
            result = chat_request(query)
            print(f"\nAsistente: {result['response']}")
            
            if result.get('relevant_sources'):
                print("\nFuentes relevantes:")
                for source in result['relevant_sources']:
                    print(f"- {source.get('title', 'Sin título')}: {source.get('link', 'Sin enlace')}")
        except Exception as e:
            print(f"\nError: {str(e)}")

if __name__ == "__main__":
    main()