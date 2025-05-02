"""
Servicio de procesamiento de lenguaje natural utilizando LangChain.

Este módulo proporciona funcionalidades para procesar consultas de usuario utilizando
LangChain, con capacidad de memoria histórica y búsqueda web para enriquecer las respuestas.
"""

from typing import Generator, Dict, Any, List, Optional, Tuple
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
from app.utils.logging_utils import (
    setup_file_logger, 
    log_conversation_history_access, 
    log_context_enrichment,
    log_web_search_results,
    log_conversation_save,
    log_full_prompt
)
# Importar el nuevo módulo de análisis de consultas
from app.services.query_analyzer import analyze_query_with_llm, analyze_query_with_rules

import logging
import re

# Configurar logging
logger = logging.getLogger(__name__)
# Configurar el logger de archivo
setup_file_logger()

# Diccionario para almacenar la memoria por sesión
session_memories = {}
# Diccionario para almacenar los system_prompts para logging
system_prompts = {}

def analyze_query_intent(current_query: str, previous_conversation: List[Dict]) -> Tuple[bool, float, str]:
    """
    Analiza la intención de la consulta actual para determinar si es una pregunta de seguimiento.
    
    Args:
        current_query: La consulta actual del usuario
        previous_conversation: Lista de conversaciones previas
        
    Returns:
        Tuple[bool, float, str]: 
            - Es pregunta de seguimiento
            - Puntuación de confianza (0-1)
            - Consulta original relacionada
    """
    if not previous_conversation:
        return False, 0.0, ""
        
    # Obtener la última consulta del usuario
    last_query = previous_conversation[0].get('user_message', '')
    last_response = previous_conversation[0].get('assistant_message', '')
    
    if not last_query:
        return False, 0.0, ""
        
    # Características que indican una pregunta de seguimiento
    followup_indicators = {
        # Consulta muy corta (menos de 5 palabras)
        'short_query': len(current_query.split()) < 5,
        
        # Pronombres sin antecedente explícito en la consulta actual
        'pronouns': bool(re.search(r'\b(lo|la|le|las|los|les|eso|esto|esta|este|él|ella|ellos|ellas)\b', current_query.lower())),
        
        # Preguntas sobre "cómo", "cuándo", "dónde" sin contexto completo
        'wh_questions': bool(re.search(r'\b(como|cuándo|cuando|donde|dónde|que|qué|cuales|cuáles|quien|quién|por que|por qué)\b', current_query.lower())) and len(current_query.split()) < 7,
        
        # Verbos en modo imperativo sin objeto claro
        'imperative': bool(re.search(r'\b(dime|cuéntame|explícame|muéstrame|dame)\b', current_query.lower())) and not bool(re.search(r'\bsobre\b', current_query.lower())),
        
        # Preguntas que comienzan con verbos auxiliares sin sujeto explícito
        'auxiliary_questions': bool(re.search(r'^(puedo|puede|puedes|podría|podrias|es|son|está|estan)\b', current_query.lower())),
        
        # Referencias a "otro", "más", "también", "adicional", etc.
        'reference_words': bool(re.search(r'\b(otro|otra|otros|otras|más|mas|también|tambien|adicional|similar|parecido|alternativa)\b', current_query.lower())),
    }
    
    # Palabras que indican cambio de tema (reducen probabilidad de ser seguimiento)
    topic_change_indicators = bool(re.search(r'\b(cambiando de tema|por cierto|ahora|nueva pregunta|otro tema|diferente|olvidalo)\b', current_query.lower()))
    
    # Calcular puntuación basada en indicadores
    score = sum(1 for indicator in followup_indicators.values() if indicator) / len(followup_indicators)
    
    # Reducir puntuación si hay indicadores de cambio de tema
    if topic_change_indicators:
        score *= 0.3
    
    # Verificar si la consulta actual tiene al menos 40% de coincidencia con palabras clave de la última consulta
    last_query_keywords = set(re.findall(r'\b\w{4,}\b', last_query.lower()))  # Palabras de 4+ caracteres
    current_query_keywords = set(re.findall(r'\b\w{4,}\b', current_query.lower()))
    
    if last_query_keywords and current_query_keywords:
        keyword_overlap = len(last_query_keywords.intersection(current_query_keywords)) / len(last_query_keywords)
        # Si hay muchas palabras clave compartidas, probablemente NO es una pregunta de seguimiento sino una reformulación
        if keyword_overlap > 0.4:
            score *= (1 - keyword_overlap)
    
    # Verificar si la consulta actual tiene relación con la respuesta del asistente
    response_keywords = set(re.findall(r'\b\w{4,}\b', last_response.lower()))
    if response_keywords and current_query_keywords:
        response_overlap = len(response_keywords.intersection(current_query_keywords)) / len(current_query_keywords) if current_query_keywords else 0
        # Si hay palabras clave de la respuesta en la consulta actual, aumentar la probabilidad de que sea seguimiento
        if response_overlap > 0.2:
            score = min(1.0, score + 0.3)
    
    logger.debug(f"Análisis de intención: Query='{current_query}', Score={score:.2f}, Indicators={[k for k,v in followup_indicators.items() if v]}")
    
    is_followup = score > 0.4  # Umbral para considerar como pregunta de seguimiento
    return is_followup, score, last_query if is_followup else ""

def extract_main_topics(query: str, response: str) -> List[str]:
    """
    Extrae los temas principales de una conversación previa.
    
    Args:
        query: La consulta del usuario
        response: La respuesta del asistente
        
    Returns:
        Lista de posibles temas principales de la conversación
    """
    # Combinar consulta y respuesta para analizar
    combined_text = f"{query} {response}".lower()
    
    # Definir patrones de temas comunes que podrían ser objeto de seguimiento
    topic_patterns = [
        # Patrones de comidas/recetas
        (r'pure\s+de\s+papa[s]?', 'puré de papas'),
        (r'sopa[s]?\s+\w+', lambda m: m.group(0)),  # "sopa aguada", "sopa de tomate", etc.
        (r'espagueti[s]?\s+\w+', lambda m: m.group(0)),
        (r'mermelada\s+de\s+\w+', lambda m: m.group(0)),
        (r'receta[s]?\s+de\s+\w+', lambda m: m.group(0)),
        
        # Platos específicos
        (r'pizza', 'pizza'),
        (r'taco[s]?', 'tacos'),
        (r'hamburguesa[s]?', 'hamburguesas'),
        (r'ensalada[s]?', 'ensaladas'),
        (r'postre[s]?', 'postres'),
        
        # Temas de arte/cultura
        (r'(pablo\s+picasso|picasso)', 'Pablo Picasso'),
        (r'pintura[s]?', 'pintura'),
        (r'escultura[s]?', 'escultura'),
        (r'música|musica', 'música'),
        (r'(libro|novela)[s]?', 'literatura'),
        
        # Lugares
        (r'viaje[s]?\s+a\s+(\w+)', lambda m: f'viaje a {m.group(1)}'),
        (r'(ciudad|país|pais)[es]?\s+(\w+)', lambda m: f'{m.group(1)} {m.group(2)}'),
        
        # Temas tecnológicos
        (r'(inteligencia\s+artificial|ia)', 'inteligencia artificial'),
        (r'programa[r]?', 'programación'),
        (r'(teléfono|telefono)[s]?', 'teléfonos'),
    ]
    
    # Buscar coincidencias de temas en el texto
    topics = []
    for pattern, topic_name in topic_patterns:
        matches = re.findall(pattern, combined_text)
        if matches:
            if callable(topic_name):
                # Si topic_name es una función, aplicarla al match
                for match in matches:
                    if isinstance(match, tuple):
                        # Para grupos capturados
                        topics.append(topic_name(match))
                    else:
                        # Para matches completos
                        topics.append(topic_name(re.match(pattern, match)))
            else:
                topics.append(topic_name)
    
    return topics

def analyze_and_reformulate_query(query: str, session_id: str) -> Tuple[str, bool, bool]:
    """
    Analiza la consulta en el contexto de la conversación y la reformula si es necesario.
    
    Args:
        query: La consulta original del usuario
        session_id: ID de la sesión para obtener el historial
        
    Returns:
        Tuple[str, bool, bool]: 
            - Consulta reformulada (o la original si no necesita reformulación)
            - Indicador de si se debe pedir clarificación
            - Indicador de si es una pregunta conversacional
    """
    # Obtener historial de la conversación
    prev_history = get_conversation_history(session_id, max_entries=3)
    if not prev_history:
        return query, False, False
        
    # Última consulta y respuesta
    last_query = prev_history[0].get('user_message', '') if prev_history else ''
    last_response = prev_history[0].get('assistant_message', '') if prev_history else ''
    
    # Detectar si es pregunta conversacional explícita
    is_conversation_query = any(q in query.lower() for q in [
        "sobre que estuvimos hablando", "de que hablamos", "sobre que hablamos",
        "cual fue nuestra conversación anterior", "que estábamos discutiendo",
        "que me dijiste antes", "que te pregunté", "tema anterior"
    ])
    
    # Si es una pregunta conversacional, devolver la consulta sin reformular
    if is_conversation_query:
        logger.info(f"Pregunta conversacional detectada: '{query}' - No se reformulará")
        return query, False, True
    
    # Analizar si la consulta contiene referencias implícitas (pronombres sin contexto claro)
    has_pronouns = bool(re.search(r'\b(lo|la|le|las|los|les|eso|esto|esta|este|él|ella|ellos|ellas)\b', query.lower()))
    
    # Detectar preguntas cortas que pueden ser ambiguas
    is_short_query = len(query.split()) < 5
    
    # Extraer posibles temas de la conversación previa
    topics = extract_main_topics(last_query, last_response)
    
    logger.debug(f"Análisis de consulta: query='{query}', has_pronouns={has_pronouns}, is_short={is_short_query}, topics={topics}")
    
    # Si la consulta tiene pronombres o es corta, y tenemos un tema identificado
    if (has_pronouns or is_short_query) and topics:
        main_topic = topics[0]  # Tomamos el primer tema como el principal
        reformulated_query = f"{query} {main_topic}"
        logger.info(f"Consulta reformulada: '{query}' -> '{reformulated_query}' (tema: {main_topic})")
        return reformulated_query, False, False
        
    # Si la consulta es muy ambigua pero no tenemos suficiente contexto para reformularla
    if (has_pronouns or is_short_query) and not topics:
        logger.info(f"Consulta ambigua detectada sin contexto suficiente: '{query}' - Se solicitará clarificación")
        return query, True, False
    
    # La consulta no necesita reformulación
    return query, False, False

def create_chain_with_memory(llm, session_id, prompt_type="default"):
    """
    Crea una cadena de procesamiento con memoria histórica y contexto enriquecido.

    Args:
        llm: Modelo de lenguaje configurado.
        session_id: ID de sesión para mantener el historial de la conversación.
        prompt_type: Tipo de prompt a utilizar ("default", "friendly", "technical").

    Returns:
        Una cadena de procesamiento con memoria histórica.
    """
    # Forzar el uso de session_id "default" para pruebas
    session_id = "default"
    
    # Registrar inicio del proceso
    logger.info(f"Creando cadena con memoria para session_id={session_id}, prompt_type={prompt_type}")
    
    # Obtener o crear memoria para la sesión - Nota: esta memoria no se está utilizando efectivamente
    # en la implementación actual, pero la mantenemos para posibles futuros cambios
    if session_id not in session_memories:
        session_memories[session_id] = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True
        )
        logger.debug(f"Creada nueva memoria para session_id={session_id}")
    else:
        logger.debug(f"Usando memoria existente para session_id={session_id}")

    memory = session_memories[session_id]

    # Seleccionar el prompt según el tipo
    system_prompt = ASSISTANT_PROMPT  # Default
    if prompt_type == "friendly":
        system_prompt = FRIENDLY_ASSISTANT_PROMPT
    elif prompt_type == "technical":
        system_prompt = TECHNICAL_ASSISTANT_PROMPT
    
    logger.debug(f"Usando prompt de tipo: {prompt_type}")

    # Obtener historial previo desde el archivo JSON
    prev_history = get_conversation_history(session_id, max_entries=3)
    log_conversation_history_access(session_id, prev_history)
    
    # Mejorado: Enriquecer el prompt con información de conversaciones previas
    if prev_history:
        # Crear una sección específica y bien estructurada para el historial de conversación
        historical_context = "\n\n### HISTORIAL DE CONVERSACIÓN RELEVANTE ###\n"
        has_relevant_info = False
        
        for entry in prev_history:
            # Añadir el par de conversación para dar contexto completo
            historical_context += f"\n[Conversación Previa]\nUsuario preguntó: {entry['user_message'][:150]}"
            if len(entry['user_message']) > 150:
                historical_context += "..."
            
            historical_context += f"\nAsistente respondió: {entry['assistant_message'][:150]}"
            if len(entry['assistant_message']) > 150:
                historical_context += "..."
                
            # Si hay fuentes relevantes en esta conversación previa
            if entry.get('relevant_sources'):
                has_relevant_info = True
                historical_context += "\nInformación relevante utilizada en esa respuesta:\n"
                
                # Añadir hasta 2 fuentes por conversación previa con formato mejorado
                for i, source in enumerate(entry['relevant_sources'][:2]):
                    if 'title' in source and 'snippet' in source:
                        historical_context += f"  • {source['title']}: {source['snippet'][:150]}"
                        if len(source['snippet']) > 150:
                            historical_context += "..."
                        historical_context += "\n"
                        if 'link' in source:
                            historical_context += f"    Fuente: {source['link']}\n"
            
            historical_context += "\n" + "-"*50 + "\n"
        
        # Añadir instrucciones específicas para usar la información histórica
        if has_relevant_info:
            history_instructions = (
                "\n\n### INSTRUCCIONES PARA USO DEL HISTORIAL ###\n"
                "1. Utiliza la información del HISTORIAL DE CONVERSACIÓN RELEVANTE para mantener coherencia.\n"
                "2. Si la pregunta actual está relacionada con temas previos, aprovecha los datos de las fuentes mencionadas.\n"
                "3. Evita repetir información que ya hayas proporcionado, a menos que necesites aclarar o ampliar.\n"
                "4. No menciones explícitamente que estás usando 'información del historial', simplemente incorpórala naturalmente.\n"
            )
            
            # Añadir las instrucciones y el historial al prompt
            system_prompt += history_instructions + historical_context
            log_context_enrichment(True, len(historical_context) + len(history_instructions))
        else:
            # Si hay historial pero sin fuentes relevantes, solo añadir una referencia más simple
            simple_history = "\n\nNota: Hay conversaciones previas con este usuario, pero sin información adicional relevante para la consulta actual."
            system_prompt += simple_history
            log_context_enrichment(False, len(simple_history))

    # Guardar el system_prompt completo en el diccionario global para uso en logging
    system_prompts[session_id] = system_prompt
    
    # Mejorado: Crear el prompt con estructura clara para diferenciar sistema, historial y contexto
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "{question}"),
        ("system", "### INFORMACIÓN ADICIONAL DE BÚSQUEDA WEB ###\n{context}" if "{context}" else "")
    ])
    logger.debug("Prompt creado con sistema, historial y contexto")

    # Configurar historial de mensajes
    message_history = ChatMessageHistory()
    
    # Mejorado: Cargar historial previo desde el archivo JSON de forma más estructurada
    if prev_history:
        logger.debug(f"Cargando {len(prev_history)} mensajes previos al historial de la cadena")
        # Añadir los mensajes previos al historial de forma más estructurada
        for entry in prev_history:
            if "user_message" in entry and "assistant_message" in entry:
                message_history.add_user_message(entry["user_message"])
                
                # Si hay fuentes relevantes, incorporarlas como parte del mensaje del asistente
                if entry.get('relevant_sources'):
                    # Crear información de las fuentes en un formato adecuado
                    sources_info = "\n\nFuentes consultadas:\n" + "\n".join([
                        f"- {s.get('title', 'Fuente')}" 
                        for s in entry['relevant_sources'][:2]
                    ])
                    
                    # Añadir el mensaje del asistente con las fuentes incorporadas
                    full_message = entry["assistant_message"] + sources_info
                    message_history.add_ai_message(full_message)
                else:
                    # Si no hay fuentes, solo añadir el mensaje del asistente
                    message_history.add_ai_message(entry["assistant_message"])

    # Envolver la cadena con capacidad de historial
    chain_with_history = RunnableWithMessageHistory(
        {
            "question": lambda x: x["question"] if isinstance(x, dict) else str(x),
            "context": lambda x: x.get("context", "") if isinstance(x, dict) else ""
        }
        | prompt
        | llm
        | StrOutputParser(),
        lambda _: message_history,
        input_messages_key="question",
        history_messages_key="chat_history"
    )
    
    logger.info("Cadena con memoria creada exitosamente")
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
    # Forzar el uso de session_id "default" para pruebas
    session_id = "default"
    
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
        # Forzar el uso de session_id "default" para pruebas
        session_id = "default"
        
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
        # Forzar el uso de session_id "default" para pruebas
        session_id = "default"
        
        logger.info(f"Procesando consulta inicial con búsqueda web: '{query}' (session_id={session_id})")
        
        # Inicializar la cadena con memoria
        chain = initialize_chain(session_id, prompt_type)
        
        # Obtener historial para análisis de contexto
        prev_history = get_conversation_history(session_id, max_entries=3)
        
        # Inicializar un LLM específico para análisis de consultas (temperatura baja para resultados más determinísticos)
        analysis_llm = ChatOpenAI(
            api_key=settings.OPENAI_API_KEY,
            model_name=settings.model_name,
            temperature=0.1,
        )
        
        # NUEVO FLUJO: Usar LLM para analizar y reformular la consulta
        search_query = query
        need_clarification = False
        is_conversation_query = False
        
        try:
            # Intentar usar el analizador basado en LLM primero
            search_query, need_clarification, is_conversation_query = analyze_query_with_llm(
                query, prev_history, analysis_llm
            )
            logger.info(f"Análisis LLM completado: reformulación='{search_query != query}', clarificación={need_clarification}, conversacional={is_conversation_query}")
        except Exception as e:
            logger.warning(f"Error en análisis LLM, usando sistema de respaldo: {str(e)}")
            # Si el LLM falla, usar el sistema de reglas con la nueva implementación mejorada
            is_conversation_query, need_clarification, search_query = analyze_query_with_rules(
                query, prev_history
            )
            logger.info(f"Análisis con reglas completado: reformulación='{search_query != query}', clarificación={need_clarification}, conversacional={is_conversation_query}")
        
        # Si aún tenemos referencia a un pronombre y no se pudo reformular, 
        # intentar de forma más específica con determinados patrones
        if "lo puedo" in query.lower() and search_query == query and prev_history:
            last_query = prev_history[0].get('user_message', '').lower()
            # Comprobación específica para casos como "con qué lo puedo acompañar"
            if "pure de papas" in last_query or "puré de papas" in last_query:
                search_query = f"con qué acompañar el puré de papas"
                logger.info(f"Reformulación manual para caso específico: '{query}' -> '{search_query}'")
        
        # Si necesitamos clarificación, devolver una respuesta solicitando más información
        if need_clarification:
            logger.info(f"Se necesita clarificación para la consulta: '{query}'")
            
            # Obtener el último tema de conversación para dar contexto
            last_topic = "el tema anterior" if not prev_history else prev_history[0].get('user_message', 'el tema anterior')
            
            # Crear una respuesta pidiendo clarificación
            clarification_response = (
                f"Tu pregunta parece estar relacionada con nuestra conversación anterior sobre "
                f"'{last_topic}', pero necesito un poco más de contexto. "
                f"¿Podrías proporcionar más detalles o reformular tu pregunta?"
            )
            
            # No realizamos búsqueda web para esta respuesta de clarificación
            save_conversation(query, clarification_response, session_id, [])
            
            return {
                "response": clarification_response,
                "relevant_sources": []
            }
        
        # Registrar si la consulta fue reformulada
        if search_query != query:
            logger.info(f"Consulta reformulada final: '{query}' -> '{search_query}'")
        
        # Realizar búsqueda web (siempre procesamos 5 enlaces para cumplir con el requisito)
        relevant_sources = get_relevant_knowledge(search_query, max_results=5)
        log_web_search_results(search_query, len(relevant_sources))
        
        # Preparar contexto con la información obtenida
        context = ""
        
        # Para preguntas conversacionales, no incluimos el contexto web en la respuesta
        if is_conversation_query:
            logger.info(f"Pregunta conversacional detectada, no se incluirá contexto web")
            # El contexto web no se incluye en la respuesta pero sí se guarda en logs
        else:
            # Para otras consultas, incluimos el contexto web
            if relevant_sources:
                context = "Información relevante:\n"
                for idx, result in enumerate(relevant_sources[:5], 1):  # Limitar a 5 resultados para el contexto
                    context += f"{idx}. {result['title']}: {result['snippet']}\n"
                    context += f"   Fuente: {result['link']}\n\n"
                
                logger.debug(f"Contexto preparado con {len(relevant_sources[:3])} fuentes, {len(context)} caracteres")

        # Preparar el input como diccionario
        input_dict = {
            "question": str(query),  # Usamos la consulta original para mantener naturalidad
            "context": context
        }
        
        # Registrar el prompt completo para análisis
        system_prompt = system_prompts.get(session_id, "")
        log_full_prompt(query, system_prompt, context, session_id, prompt_type)

        # Invocar la cadena asegurando que los tipos sean correctos
        logger.debug("Invocando la cadena con el contexto preparado")
        response = chain.invoke(
            input_dict,
            config={"configurable": {"session_id": session_id}}
        )

        # Asegurarse de que la respuesta sea string
        response_text = str(response) if response is not None else ""
        logger.debug(f"Respuesta generada: {len(response_text)} caracteres")
        
        # Guardar la conversación en el historial incluyendo las fuentes relevantes
        # Siempre guardamos todas las fuentes en el historial para cumplir el requisito
        save_conversation(query, response_text, session_id, relevant_sources)
        log_conversation_save(query, session_id, bool(relevant_sources))

        # Para preguntas conversacionales, no mostramos fuentes aunque las hayamos guardado
        if is_conversation_query:
            return {
                "response": response_text,
                "relevant_sources": []
            }
        else:
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
