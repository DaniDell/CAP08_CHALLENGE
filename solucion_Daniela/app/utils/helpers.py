import json
import os


def save_conversation(user_message, assistant_message, session_id="default", relevant_sources=None, file_path="data/historical_conversation.json"):
    """
    Guarda una interacción de conversación en el historial.

    :param user_message: Mensaje del usuario
    :param assistant_message: Respuesta del asistente
    :param session_id: Identificador de la sesión del usuario (default por defecto)
    :param relevant_sources: Lista de fuentes relevantes encontradas en la búsqueda web
    :param file_path: Ruta del archivo JSON de historial
    """
    os.makedirs(os.path.dirname(file_path), exist_ok=True)  # Crear directorio si no existe

    # Crear el objeto de mensaje
    conversation_entry = {
        "session_id": session_id,
        "timestamp": import_datetime_if_needed(),
        "user_message": user_message,
        "assistant_message": assistant_message,
        "relevant_sources": relevant_sources or []  # Guardar las fuentes relevantes
    }

    # Leer datos existentes si el archivo ya existe
    if os.path.exists(file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as file:
                existing_data = json.load(file)
        except json.JSONDecodeError:
            existing_data = []  # Si el archivo está vacío o corrupto, inicializar como lista vacía
    else:
        existing_data = []

    # Agregar la nueva conversación
    existing_data.append(conversation_entry)

    # Guardar los datos actualizados
    with open(file_path, "w", encoding="utf-8") as file:
        json.dump(existing_data, file, ensure_ascii=False, indent=4)

    return True

def get_conversation_history(session_id="default", max_entries=10, file_path="data/historical_conversation.json"):
    """
    Recupera el historial de conversación de una sesión específica.

    :param session_id: Identificador de la sesión del usuario (default por defecto)
    :param max_entries: Número máximo de entradas a recuperar (últimas N conversaciones)
    :param file_path: Ruta del archivo JSON de historial
    :return: Lista de diccionarios con las conversaciones incluyendo fuentes relevantes si existen
    """
    if not os.path.exists(file_path):
        return []

    try:
        with open(file_path, "r", encoding="utf-8") as file:
            all_conversations = json.load(file)
    except json.JSONDecodeError:
        return []

    # Filtrar por session_id
    session_conversations = [conv for conv in all_conversations if conv.get("session_id") == session_id]
    
    # Asegurarse de que todas las conversaciones tengan el campo relevant_sources
    for conv in session_conversations:
        if "relevant_sources" not in conv:
            conv["relevant_sources"] = []
    
    # Devolver las últimas N conversaciones
    return session_conversations[-max_entries:] if max_entries > 0 else session_conversations

def import_datetime_if_needed():
    """Helper function to import datetime and return current timestamp"""
    from datetime import datetime
    return datetime.now().isoformat()