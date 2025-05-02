"""
Módulo para análisis y reformulación de consultas usando LLM.

Este módulo proporciona funcionalidades para analizar el contexto conversacional
y reformular consultas para búsquedas más relevantes usando un modelo de lenguaje.
"""

import json
import logging
import re
from typing import List, Dict, Any, Tuple, Optional

# Configurar logging
logger = logging.getLogger(__name__)

def analyze_query_with_llm(
    query: str, 
    conversation_history: List[Dict[str, Any]], 
    llm
) -> Tuple[str, bool, bool]:
    """
    Analiza la consulta del usuario usando un LLM para determinar si es una pregunta de seguimiento
    y reformularla para obtener mejores resultados de búsqueda.
    
    Args:
        query: La consulta original del usuario
        conversation_history: Historial de conversaciones previas
        llm: Modelo de lenguaje a utilizar para el análisis
        
    Returns:
        Tuple[str, bool, bool]:
            - Consulta reformulada para búsqueda web (o la original si no se requiere reformulación)
            - Indicador de si se debe pedir clarificación
            - Indicador de si es una pregunta sobre la conversación
    """
    # Si no hay historial, no podemos hacer análisis de contexto
    if not conversation_history:
        return query, False, False
    
    # Preparar la representación del historial para el prompt
    formatted_history = format_conversation_history(conversation_history)
    
    # Crear el prompt para el LLM con instrucciones mucho más específicas
    system_prompt = """
    Tu tarea es analizar una consulta del usuario en el contexto de una conversación previa.
    Presta mucha atención a los siguientes casos:

    1. CONSULTAS SOBRE LA CONVERSACIÓN:
       - Preguntas como "¿de qué estábamos hablando?" o "¿qué me dijiste antes?"
       - Estas preguntas son sobre la conversación misma.

    2. PREGUNTAS DE SEGUIMIENTO:
       - Consultas que dependen del contexto anterior como "¿con qué lo puedo acompañar?" (refiriéndose a un plato mencionado antes)
       - Frases como "cuéntame más", "¿qué más?", "sigue", etc.
       - Preguntas con pronombres como "lo", "la", "eso" sin un antecedente claro en la pregunta
       - Estas preguntas generalmente deben reformularse para incluir el contexto

    3. CONSULTAS AMBIGUAS:
       - Preguntas demasiado cortas o vagas que no tienen sentido sin contexto previo
       - Estas pueden requerir clarificación

    4. CONSULTAS INDEPENDIENTES:
       - Preguntas completas que introducen un nuevo tema
    
    Para las preguntas de seguimiento, analiza el contexto y reformula la consulta para que sea clara y completa. 
    Por ejemplo, si hablaban de "puré de papas" y el usuario pregunta "¿con qué lo puedo acompañar?", 
    reformula la consulta como "¿con qué puedo acompañar el puré de papas?".
    """
    
    query_prompt = f"""
    Historial de conversación reciente:
    {formatted_history}
    
    Consulta actual del usuario: "{query}"
    
    Analiza cuidadosamente la consulta en relación al historial y responde con un JSON con este formato exacto:
    {{
        "is_conversation_query": true/false,  // ¿Es una pregunta sobre la conversación misma?
        "needs_clarification": true/false,   // ¿Necesita clarificación por ser ambigua?
        "reformulated_query": "consulta reformulada para búsqueda web o vacío si no es necesario"
    }}
    
    Presta especial atención a consultas con pronombres o referencias implícitas a temas previos, 
    y REFORMULA siempre que la consulta dependa de contexto previo para ser comprendida.
    
    Responde SOLAMENTE con el objeto JSON, sin texto adicional.
    """
    
    try:
        # Registrar información importante para depuración
        logger.debug(f"Enviando consulta a LLM para análisis: '{query}'")
        if conversation_history:
            logger.debug(f"Última consulta en historial: '{conversation_history[0].get('user_message', '')}'")
        
        # Invocar el LLM para analizar la consulta
        response = llm.invoke(system_prompt + "\n\n" + query_prompt)
        logger.debug(f"Respuesta del LLM para análisis: {response}")
        
        # Intentar extraer el JSON de la respuesta
        analysis = extract_json_from_response(response)
        if not analysis:
            # Si no se puede extraer el JSON, usar valores predeterminados seguros
            logger.warning("No se pudo extraer JSON válido del análisis LLM")
            return query, False, False
        
        # Extraer los resultados del análisis
        is_conversation_query = analysis.get("is_conversation_query", False)
        needs_clarification = analysis.get("needs_clarification", False)
        reformulated_query = analysis.get("reformulated_query", "")
        
        # Registrar el resultado del análisis
        if reformulated_query:
            logger.info(f"Consulta reformulada por LLM: '{query}' -> '{reformulated_query}'")
        if is_conversation_query:
            logger.info(f"LLM identificó la consulta como pregunta sobre la conversación: '{query}'")
        if needs_clarification:
            logger.info(f"LLM indica que la consulta requiere clarificación: '{query}'")
        
        # Devolver la consulta reformulada si existe, de lo contrario la original
        return reformulated_query if reformulated_query else query, needs_clarification, is_conversation_query
        
    except Exception as e:
        logger.error(f"Error durante el análisis LLM de la consulta: {str(e)}", exc_info=True)
        # En caso de error, devolver valores seguros predeterminados
        return query, False, False

def format_conversation_history(history: List[Dict[str, Any]]) -> str:
    """
    Formatea el historial de conversación para incluirlo en el prompt del LLM.
    
    Args:
        history: Lista de entradas del historial de conversación
        
    Returns:
        String con el historial formateado
    """
    formatted_history = ""
    
    # Usar solo las últimas 5 entradas para mantener el contexto relevante y reciente
    for i, entry in enumerate(history[:3]):
        user_message = entry.get("user_message", "")
        assistant_message = entry.get("assistant_message", "")
        
        formatted_history += f"--- Turno de conversación {i+1} ---\n"
        
        if user_message:
            formatted_history += f"Usuario: {user_message}\n"
            
        if assistant_message:
            # Incluir solo los primeros 200 caracteres de la respuesta para no sobrecargar el contexto
            formatted_history += f"Asistente: {assistant_message[:200]}"
            if len(assistant_message) > 200:
                formatted_history += "..."
            formatted_history += "\n"
        
        # Incluir fuentes relevantes si están disponibles
        if 'relevant_sources' in entry and entry['relevant_sources']:
            formatted_history += "Temas principales mencionados: "
            
            # Extraer temas de los títulos de las fuentes
            topics = []
            for source in entry['relevant_sources'][:3]:  # Limitar a 3 fuentes
                if 'title' in source:
                    title = source['title']
                    # Extraer palabras clave del título
                    topics.append(title.split(':')[0] if ':' in title else title[:30])
            
            formatted_history += ", ".join(topics) + "\n"
        
        formatted_history += "\n"  # Separación entre turnos de conversación
    
    return formatted_history

def extract_json_from_response(response) -> Optional[Dict[str, Any]]:
    """
    Extrae un objeto JSON de la respuesta del LLM, manejando casos donde el LLM
    podría añadir texto adicional antes o después del JSON.
    
    Args:
        response: Respuesta del LLM (puede ser string o AIMessage)
        
    Returns:
        Diccionario extraído del JSON o None si no se puede extraer
    """
    # Extraer el contenido si es un objeto AIMessage
    response_text = response.content if hasattr(response, 'content') else str(response)
    
    try:
        # Intentar cargar directamente como JSON
        return json.loads(response_text)
    except json.JSONDecodeError:
        # Intentar encontrar el JSON usando expresión regular
        pattern = r'{[\s\S]*}'
        match = re.search(pattern, response_text)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                # Si todavía falla, limpiar y normalizar
                json_str = match.group(0)
                # Reemplazar valores booleanos en texto por formato JSON válido
                json_str = re.sub(r'\btrue\b', 'true', json_str)
                json_str = re.sub(r'\bfalse\b', 'false', json_str)
                try:
                    return json.loads(json_str)
                except json.JSONDecodeError:
                    return None
        return None

# Función de respaldo basada en reglas en caso de que el LLM falle
def analyze_query_with_rules(query: str, conversation_history: List[Dict[str, Any]] = None) -> Tuple[bool, bool, str]:
    """
    Analiza la consulta usando reglas básicas para determinar si es una pregunta sobre la 
    conversación o si necesita clarificación. Esta función sirve como respaldo cuando el LLM falla.
    
    Args:
        query: La consulta del usuario
        conversation_history: Lista de conversaciones previas (opcional)
        
    Returns:
        Tuple[bool, bool, str]:
            - Indicador de si es una pregunta sobre la conversación
            - Indicador de si necesita clarificación
            - Consulta reformulada (o la original si no se requiere reformulación)
    """
    query_lower = query.lower()
    
    # Detectar si es una pregunta sobre la conversación anterior
    conversation_patterns = [
        "sobre que estuvimos hablando", 
        "de que hablamos", 
        "sobre que hablamos",
        "cual fue nuestra conversación", 
        "que estábamos discutiendo",
        "que me dijiste", 
        "que te pregunté", 
        "tema anterior"
    ]
    
    is_conversation_query = any(pattern in query_lower for pattern in conversation_patterns)
    
    # Detectar consultas muy cortas o ambiguas que podrían necesitar clarificación
    is_too_short = len(query.split()) <= 2 and not is_conversation_query
    has_pronouns_without_context = bool(re.search(r'\b(lo|la|le|las|los|les|eso|esto|esta|este)\b', query_lower)) and len(query.split()) < 7
    
    needs_clarification = is_too_short or has_pronouns_without_context
    
    # Intentar reformular si tenemos historial y hay pronombres o referencia implícita
    reformulated_query = query
    if conversation_history and has_pronouns_without_context and len(conversation_history) > 0:
        # Extracción rudimentaria de tema anterior
        last_query = conversation_history[0].get('user_message', '')
        last_response = conversation_history[0].get('assistant_message', '')
        
        # Buscar temas específicos en la consulta anterior
        food_patterns = [
            (r'pure\s+de\s+papa[s]?', 'puré de papas'),
            (r'pizza', 'pizza'),
            (r'sopa\s+\w+', lambda m: m.group(0)),
            (r'hamburguesa[s]?', 'hamburguesas'),
            (r'espagueti', 'espagueti'),
            (r'pasta', 'pasta')
        ]
        
        for pattern, replacement in food_patterns:
            if re.search(pattern, last_query.lower()) or re.search(pattern, last_response.lower()):
                if callable(replacement):
                    match = re.search(pattern, last_query.lower() or last_response.lower())
                    if match:
                        topic = match.group(0)
                    else:
                        continue
                else:
                    topic = replacement
                    
                # Si tenemos "con que lo puedo acompañar" y el tema es comida, hacer una reformulación específica
                if "con que lo puedo" in query_lower or "con qué lo puedo" in query_lower:
                    reformulated_query = f"con qué puedo acompañar {topic}"
                    logger.info(f"Reformulación básica de consulta: '{query}' -> '{reformulated_query}'")
                    return is_conversation_query, False, reformulated_query
    
    return is_conversation_query, needs_clarification, query