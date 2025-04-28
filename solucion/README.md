# Chatbot de IA Conversacional con Acceso a Internet

## Descripción del Proyecto

Basado en You.com y el Bard de Google, este proyecto es un chatbot de inteligencia artificial generativa conversacional que puede acceder a internet. Está diseñado para proporcionar información en tiempo real y entablar conversaciones con los usuarios. Para mejorar su rendimiento, el chatbot utiliza una base de datos vectorial de Redis (caché de Redis Vector DB) para almacenar información previamente recuperada, reduciendo la necesidad de consultar internet repetidamente por los mismos datos. También aprovecha la API de Búsqueda de Google para consultar sitios web.

## Primeros Pasos

Sigue estos pasos para ejecutar el chatbot localmente en tu máquina:

1. **Configura tu Entorno**:

    - Crea un archivo `.env` copiando el proporcionado `.env.example`. Este archivo debe contener las siguientes variables de entorno:
        - `HEADER_ACCEPT_ENCODING`: Establézcalo en "gzip".
        - `HEADER_USER_AGENT`: Usa una cadena de agente de usuario, por ejemplo, "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36 (gzip)".
        - `GOOGLE_API_HOST`: Establece el host de la API de Google en "https://www.googleapis.com/customsearch/v1?".
        - `GOOGLE_FIELDS`: Define los campos que deseas recuperar de Google. Ejemplo: "items(title, displayLink, link, snippet,pagemap/cse_thumbnail)".
        - `GOOGLE_API_KEY`: Obtén una clave API de Google de [Google Custom Search](https://developers.google.com/custom-search/v1/overview).
        - `GOOGLE_CX`: Puedes obtener tu ID de Motor de Búsqueda Personalizado (CX) de la misma página de Google Custom Search.
        - `OPENAI_API_KEY`: Obtén una clave API de [OpenAI](https://openai.com/blog/openai-api).

    - Debes estar dentro de `/solucion`. Crea tu entorno:
    ```bash
    pipenv shell
    pip install -r requirements.txt
    ```

2. **Construye y Ejecuta la Aplicación**:

    - Ejecuta los siguientes comandos para construir e iniciar la aplicación:

    ```bash
    python3 src/orchestrator/main.py 
    ```

    Y comienza a chatear.
