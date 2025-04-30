"""
Servicio de procesamiento de lenguaje natural utilizando LangChain.
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

from app.utils.knowledge_base import load_knowledge_base
from app.config.settings import settings
from app.utils.knowledge_base import get_relevant_knowledge as kb_get_relevant_knowledge

import requests
import json

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
        if isinstance(docs, (list, tuple)):
            return "\n\n".join(str(doc.page_content) if hasattr(doc, 'page_content') else str(doc) for doc in docs)
        return str(docs)

    # Pipeline completo usando RunnableLambda para asegurar el tipo correcto
    chain = (
        {
            "context": RunnableLambda(lambda x: format_docs(context_retriever.get_relevant_documents(x["question"]))),
            "question": RunnableLambda(lambda x: x["question"] if isinstance(x, dict) else str(x))
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
        retriever = vectorstore.as_retriever()
    except Exception:
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
        retriever = vectorstore.as_retriever()

    # Configuración de la memoria
    memory = ConversationBufferMemory(
        memory_key="chat_history",
        return_messages=True,
        output_key="output"
    )

    # Crear la cadena completa
    chain = create_retrieval_chain(llm, retriever)
    
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
            f"Información: {item['snippet']}"
            for item in relevant_data[:5]
        ])
        
        # Preparar el input como diccionario
        input_dict = {
            "question": str(query),
            "context": str(web_context)
        }
        
        # Invocar la cadena asegurando que los tipos sean correctos
        response = chain.invoke(
            input_dict,
            config={"configurable": {"session_id": session_id}}
        )
        
        # Asegurarse de que la respuesta sea string
        response_text = str(response) if response is not None else ""
        
        # Formatear las citas
        citations = "\n".join([
            f"- {item['title']}: {item['link']}"
            for item in relevant_data[:5]
        ])
        
        final_response = response_text
        if citations:
            final_response += "\n\nEnlaces consultados:\n" + citations
        
        return {
            "response": final_response,
            "relevant_sources": relevant_data[:5]
        }
    except Exception as e:
        return {
            "response": f"Error al procesar la consulta: {str(e)}",
            "relevant_sources": []
        }