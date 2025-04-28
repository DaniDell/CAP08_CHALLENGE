import sys
import os
import requests
import re
from bs4 import BeautifulSoup

# Agregar el directorio raíz del proyecto al PYTHONPATH
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import settings

def search_google(query, api_key, cx):
    """
    Realiza una búsqueda en Google utilizando la API de Google Custom Search.

    :param query: Término de búsqueda.
    :param api_key: Clave de API de Google.
    :param cx: ID del motor de búsqueda personalizado.
    :return: Resultados de la búsqueda en formato JSON.
    """
    url = f"https://www.googleapis.com/customsearch/v1"
    params = {
        "q": query,
        "key": api_key,
        "cx": cx,
        "num": 5  # Limitar a los primeros 5 resultados
    }

    response = requests.get(url, params=params)
    response.raise_for_status()  # Lanza una excepción si la solicitud falla
    return response.json()

def clean_text(text):
    """
    Limpia el texto eliminando contenido irrelevante como saltos de línea, espacios redundantes y caracteres especiales.

    :param text: Texto a limpiar.
    :return: Texto limpio.
    """
    # Eliminar saltos de línea y espacios redundantes
    text = re.sub(r'\s+', ' ', text)

    # Eliminar emojis y caracteres especiales
    text = re.sub(r'[\U00010000-\U0010ffff]', '', text)

    # Eliminar enlaces
    text = re.sub(r'http\S+', '', text)

    # Eliminar texto repetitivo o promocional
    text = re.sub(r'(\b\w+\b)(?=.*\b\1\b)', '', text)

    return text.strip()

def fetch_page_content(url):
    """
    Realiza una solicitud HTTP para obtener el contenido de una página web y extrae los primeros párrafos relevantes.

    :param url: URL de la página web.
    :return: Texto relevante extraído de la página.
    """
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        # Extraer los primeros párrafos relevantes
        paragraphs = soup.find_all('p')
        content = ' '.join(p.get_text() for p in paragraphs[:5])  # Limitar a los primeros 5 párrafos

        return clean_text(content)
    except Exception as e:
        print(f"Error al obtener contenido de {url}: {e}")
        return ""

def process_search_results(results):
    """
    Procesa los resultados de la búsqueda para extraer información clave y enriquecer los resúmenes.

    :param results: Resultados de la búsqueda en formato JSON.
    :return: Lista de diccionarios con título, enlace y resumen enriquecido de cada resultado.
    """
    processed_results = []
    for item in results.get("items", []):
        # Extraer información básica
        title = item.get("title")
        link = item.get("link")
        snippet = item.get("snippet")

        # Enriquecer el resumen con más contexto si está disponible
        pagemap = item.get("pagemap", {})
        additional_context = ""

        if "metatags" in pagemap:
            metatags = pagemap["metatags"][0] if pagemap["metatags"] else {}
            additional_context = metatags.get("og:description", "")

        # Combinar snippet y contexto adicional
        enriched_snippet = snippet
        if additional_context:
            enriched_snippet += f" {additional_context}"

        # Limpiar el texto del resumen
        enriched_snippet = clean_text(enriched_snippet)

        # Agregar el resultado procesado
        processed_results.append({
            "title": title,
            "link": link,
            "snippet": enriched_snippet.strip()
        })

    return processed_results

def process_search_results_with_content(results):
    """
    Procesa los resultados de la búsqueda y enriquece los resúmenes con contenido de las páginas web.

    :param results: Resultados de la búsqueda en formato JSON.
    :return: Lista de diccionarios con título, enlace y resumen enriquecido de cada resultado.
    """
    processed_results = []
    for item in results.get("items", []):
        # Extraer información básica
        title = item.get("title")
        link = item.get("link")
        snippet = item.get("snippet")

        # Obtener contenido adicional de la página web
        page_content = fetch_page_content(link)

        # Limpiar y combinar el contenido con el snippet
        enriched_snippet = snippet
        if page_content:
            enriched_snippet += f" {page_content[:1000]}..."  # Limitar a 1000 caracteres

        enriched_snippet = clean_text(enriched_snippet)

        # Agregar el resultado procesado
        processed_results.append({
            "title": title,
            "link": link,
            "snippet": enriched_snippet.strip()
        })

    return processed_results

def test_google_search():
    query = "FastAPI tutorial"
    results = search_google(query, settings.GOOGLE_API_KEY, settings.GOOGLE_CX)
    processed_results = process_search_results(results)
    for result in processed_results:
        print(result)

if __name__ == "__main__":
    test_google_search()