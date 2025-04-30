# Asistente Conversacional con LangChain

## Descripción
Este proyecto implementa un asistente conversacional utilizando LangChain y OpenAI. El asistente puede responder preguntas basándose en una base de conocimiento y mantener el contexto de la conversación.

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
```

## Ejecución

Para iniciar el servidor:
```bash
uvicorn app.main:app --reload
```

Acceder a la documentación API en: http://127.0.0.1:8000/docs

## Notas sobre compatibilidad de versiones

Este proyecto requiere versiones específicas de las bibliotecas de LangChain para funcionar correctamente. Se han actualizado las dependencias para resolver problemas de compatibilidad entre:
- langchain
- langchain-openai
- langchain-core
- langchain-community
- langchain-text-splitters

Si encuentras errores relacionados con parámetros no reconocidos (como "proxies"), asegúrate de que todas las dependencias estén actualizadas a las versiones especificadas en requirements.txt.
```

## Actualización del código si es necesario

Si después de actualizar las dependencias sigues teniendo problemas, es posible que necesites actualizar algunas partes del código para adaptarlo a las nuevas versiones de las bibliotecas. Aquí hay algunas sugerencias basadas en los cambios comunes entre versiones:

```python:app\services\langchain_service.py
# Actualiza las importaciones si es necesario
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain.memory import ConversationBufferMemory
from langchain_community.vectorstores import FAISS
from langchain.prompts import PromptTemplate, ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough, RunnableLambda
from langchain_core.output_parsers import StrOutputParser
from langchain_core.messages import HumanMessage, AIMessage

# Asegúrate de que la inicialización de ChatOpenAI sea compatible con la nueva versión
llm = ChatOpenAI(
    api_key=settings.OPENAI_API_KEY,  # Cambio de openai_api_key a api_key si es necesario
    model_name=settings.model_name,
    temperature=settings.temperature,
)
```

## Documentación adicional

También es recomendable añadir comentarios en el código para explicar los cambios realizados y documentar cualquier consideración importante para futuras actualizaciones:

```python:app\services\langchain_service.py
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