from app.config.settings import settings
import json
import os
import redis

# Configuración de Redis
redis_client = redis.StrictRedis.from_url(settings.REDIS_URL)

def load_knowledge_base():
    """
    Carga la base de conocimiento desde Redis si está disponible.
    Si Redis no está disponible, carga desde un archivo JSON.
    """
    try:
        # Intentar cargar desde Redis
        data = redis_client.get("knowledge_base")
        if data:
            return json.loads(data)
    except redis.RedisError:
        pass  # Si Redis falla, continuar con el respaldo JSON

    # Respaldo: cargar desde archivo JSON
    try:
        with open("data/knowledge_base.json", "r", encoding="utf-8") as file:
            return json.load(file)
    except FileNotFoundError:
        return []
    except Exception as e:
        raise RuntimeError(f"Error al cargar la base de conocimiento desde JSON: {e}")

def save_knowledge_base(data):
    """
    Guarda la base de conocimiento en Redis si está disponible.
    Si Redis no está disponible, guarda en un archivo JSON.
    """
    try:
        # Intentar guardar en Redis
        redis_client.set("knowledge_base", json.dumps(data))
        return
    except redis.RedisError:
        pass  # Si Redis falla, continuar con el respaldo JSON

    # Respaldo: guardar en archivo JSON
    try:
        with open("data/knowledge_base.json", "w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False, indent=4)
    except Exception as e:
        raise RuntimeError(f"Error al guardar la base de conocimiento en JSON: {e}")

def search_in_knowledge_base(query, knowledge_base):
    """
    Busca información relevante en la base de conocimiento.

    :param query: Consulta del usuario.
    :param knowledge_base: Lista de datos de la base de conocimiento.
    :return: Lista de datos relevantes que contienen el término de búsqueda.
    """
    return [
        item for item in knowledge_base
        if "snippet" in item and query.lower() in item["snippet"].lower()
    ]