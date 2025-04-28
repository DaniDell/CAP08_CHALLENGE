import json

def load_knowledge_base(file_path="data/knowledge_base.json"):
    """
    Carga la base de conocimiento desde un archivo JSON.

    :param file_path: Ruta del archivo JSON.
    :return: Lista de datos de la base de conocimiento.
    """
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            return json.load(file)
    except FileNotFoundError:
        return []
    except Exception as e:
        raise RuntimeError(f"Error al cargar la base de conocimiento: {e}")

def search_in_knowledge_base(query, knowledge_base):
    """
    Busca información relevante en la base de conocimiento.

    :param query: Consulta del usuario.
    :param knowledge_base: Lista de datos de la base de conocimiento.
    :return: Lista de datos relevantes.
    """
    return [item for item in knowledge_base if query.lower() in item["snippet"].lower()]