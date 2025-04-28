import json
import os

def save_to_json(data, file_path="data/knowledge_base.json"):
    """
    Guarda los datos en un archivo JSON, evitando duplicados.

    :param data: Lista de diccionarios a guardar.
    :param file_path: Ruta del archivo JSON.
    """
    os.makedirs(os.path.dirname(file_path), exist_ok=True)  # Crear directorio si no existe

    # Leer datos existentes si el archivo ya existe
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as file:
            existing_data = json.load(file)
    else:
        existing_data = []

    # Evitar duplicados basados en el campo "link"
    existing_links = {item["link"] for item in existing_data}
    new_data = [item for item in data if item["link"] not in existing_links]

    # Agregar los nuevos datos
    existing_data.extend(new_data)

    # Guardar los datos actualizados
    with open(file_path, "w", encoding="utf-8") as file:
        json.dump(existing_data, file, ensure_ascii=False, indent=4)

    print(f"Datos guardados en {file_path}")