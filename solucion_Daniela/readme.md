# Asistente Conversacional con LangChain

## Descripción
Este proyecto implementa un asistente conversacional utilizando LangChain y OpenAI. El asistente puede responder preguntas basándose en una base de conocimiento y mantener el contexto de la conversación. También incluye capacidades de búsqueda en la web para enriquecer las respuestas.

## Requisitos
- Python 3.8+
- Dependencias listadas en requirements.txt

## Instalación

1. Clonar el repositorio:
```bash
git clone https://github.com/DaniDell/CAP08_CHALLENGE.git
cd CAP08_CHALLENGE/solucion_Daniela
```

2. Crear y activar un entorno virtual:
```bash
python -m venv venv
# En Windows
venv\Scripts\activate
# En macOS/Linux
source venv/bin/activate
```

3. Instalar dependencias:
```bash
pip install -r requirements.txt
```

4. Configurar variables de entorno:
Crear un archivo `.env` en la raíz del proyecto con:
```
OPENAI_API_KEY=tu_clave_api_aquí
GOOGLE_API_KEY=tu_clave_google_aquí
GOOGLE_CX=tu_id_buscador_personalizado
```

## Ejecución

Para iniciar el servidor:
```bash
uvicorn app.main:app --reload
```

Acceder a la documentación API en: http://127.0.0.1:8000/docs

## Funcionalidades

- **Chat Síncrono**: Endpoint `/api/chat` para obtener respuestas completas con citas.
- **Chat en Streaming**: Endpoint `/api/chat/stream` para respuestas en tiempo real.
- **Búsqueda en la Web**: Integra resultados de búsqueda para enriquecer las respuestas.
- **Base de Conocimiento**: Respuestas basadas en un archivo JSON configurable.
- **Memoria de Conversación**: Mantiene el contexto de conversaciones previas.
- **Manejo Inteligente de Fuentes**: Muestra fuentes solo cuando son relevantes para la consulta.

## Características Avanzadas

### Procesamiento Inteligente de Búsquedas Web

El sistema procesa siempre los primeros 5 enlaces relevantes de cada consulta (cumpliendo con el requisito técnico), pero implementa una lógica para determinar cuándo mostrar estas fuentes al usuario:

1. **Para consultas normales**: Muestra todas las fuentes relevantes encontradas, priorizando las que contienen información específica y útil.

2. **Para consultas conversacionales** (como "¿de qué hablamos antes?"): 
   - Procesa igualmente los 5 enlaces para cumplir con el requisito técnico
   - Guarda esta información en los logs para análisis y seguimiento
   - No muestra las fuentes web al usuario, ya que no son relevantes para este tipo de consultas
   - Se centra en recuperar el contexto previo de la conversación

### Estructura Mejorada de Prompts

El sistema incluye tres variantes de prompts con instrucciones especializadas:

1. **ASSISTANT_PROMPT (Default)**: Para respuestas concisas y directas con tono neutral.
2. **FRIENDLY_ASSISTANT_PROMPT**: Para respuestas con tono conversacional y amigable.
3. **TECHNICAL_ASSISTANT_PROMPT**: Para respuestas técnicas detalladas y precisas.

Todos los prompts incluyen instrucciones específicas para:
- Integrar naturalmente la información del contexto
- Utilizar fuentes solo cuando añadan valor real
- Manejar preguntas sobre la conversación anterior priorizando el historial

## Notas sobre compatibilidad de versiones

Este proyecto requiere versiones específicas de las bibliotecas de LangChain para funcionar correctamente. Se han actualizado las dependencias para resolver problemas de compatibilidad entre:
- langchain
- langchain-openai
- langchain-core
- langchain-community
- langchain-text-splitters

Si encuentras errores relacionados con parámetros no reconocidos (como "proxies"), asegúrate de que todas las dependencias estén actualizadas a las versiones especificadas en requirements.txt.

## Actualización del código si es necesario

Si después de actualizar las dependencias sigues teniendo problemas, es posible que necesites actualizar algunas partes del código para adaptarlo a las nuevas versiones de las bibliotecas. Aquí hay algunas sugerencias basadas en los cambios comunes entre versiones:

```python
# Actualiza las importaciones si es necesario
def initialize_chain():
    """
    Inicializa la cadena de procesamiento de LangChain.
    """
    llm = ChatOpenAI(
        api_key=settings.OPENAI_API_KEY,  # Cambio de openai_api_key a api_key si es necesario
        model_name=settings.model_name,
        temperature=settings.temperature,
    )
```

## Documentación adicional

También es recomendable añadir comentarios en el código para explicar los cambios realizados y documentar cualquier consideración importante para futuras actualizaciones:

```python
"""
Servicio de procesamiento de lenguaje natural utilizando LangChain.

Este módulo implementa la lógica de procesamiento de consultas utilizando el framework LangChain.
Proporciona funcionalidades para:
- Inicialización y gestión de la cadena de procesamiento
- Manejo de consultas en modo streaming
- Generación de respuestas con citas

Nota sobre versiones:
Este código ha sido actualizado para funcionar con:
- langchain >= 0.1.20
- langchain-openai >= 0.3.14
- langchain-core >= 0.3.56
Si se actualizan estas dependencias, revisar la compatibilidad de los parámetros
en la inicialización de ChatOpenAI y otros componentes.
"""
```