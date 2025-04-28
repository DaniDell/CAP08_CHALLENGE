from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate

def generate_response_with_citations(context, query, relevant_data):
    """
    Genera una respuesta utilizando Langchain y agrega citas automáticas.

    :param context: Contexto relevante para la consulta.
    :param query: Consulta del usuario.
    :param relevant_data: Datos relevantes de la base de conocimiento.
    :return: Respuesta generada con citas automáticas.
    """
    # Configurar Langchain con OpenAI
    llm = ChatOpenAI(temperature=0.7)
    prompt = PromptTemplate(
        input_variables=["context", "query"],
        template="""
Eres un asistente conversacional experto en responder preguntas de manera clara, amigable y basada en evidencia. Utiliza únicamente la información proporcionada en el contexto.

Instrucciones:
- Responde como si estuvieras teniendo una conversación con un humano.
- Integra las fuentes de manera natural en el texto (por ejemplo: "Según el video de Karlos Arguiñano...").
- Sé claro, profesional y directo, pero mantén un tono accesible y amigable.
- Usa puntos aparte para organizar las ideas y hacer que la respuesta sea más fácil de leer.
- Si falta información en el contexto, indícalo de manera amable.

Ejemplo de respuesta:
---
Contexto: "Video de Karlos Arguiñano sobre cómo freír un huevo perfecto."
Pregunta: "¿Cuál es el truco para hacer un huevo frito perfecto?"
Respuesta:
"Para hacer un huevo frito perfecto, Karlos Arguiñano recomienda calentar el aceite a la temperatura adecuada y verter el huevo con cuidado para lograr una clara crujiente sin romper la yema. También sugiere usar aceite de oliva para realzar el sabor. ¡Es un truco sencillo pero efectivo!"

Ahora responde usando el siguiente contexto:

Contexto:
{context}

Pregunta:
{query}

Respuesta:
"""
    )

    # Generar respuesta
    formatted_prompt = prompt.format(context=context, query=query)
    raw_response = llm.invoke(formatted_prompt)

    # Extraer solo el contenido relevante
    response_content = raw_response['content'] if isinstance(raw_response, dict) and 'content' in raw_response else str(raw_response)

    # Agregar enlaces relevantes
    citations = "\n".join([
        f"- {item['title']}: {item['link']}"
        for item in relevant_data[:5]
    ])

    # Formatear la respuesta final
    response_with_citations = f"{response_content}\n\nEnlaces consultados:\n{citations}"

    return response_with_citations