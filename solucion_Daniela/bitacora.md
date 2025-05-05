# Bitácora del Proyecto

## Resumen del Proyecto
Este proyecto consiste en un chatbot interactivo que opera a través de una consola y utiliza una API para realizar búsquedas web y proporcionar respuestas en tiempo real. El objetivo principal es ofrecer una experiencia conversacional eficiente, citando fuentes relevantes y reformulando consultas para mejorar la precisión de las respuestas.

---

## Cambios y Mejoras Implementadas

### 1. **Corrección de Bug en `extract_json_from_response`**
- **Problema:** La función `extract_json_from_response` fallaba al procesar objetos `AIMessage` provenientes de LangChain, lo que impedía reformular consultas correctamente.
- **Solución:** Se actualizó la función para manejar tanto cadenas de texto como objetos `AIMessage`, extrayendo correctamente el contenido JSON.

### 2. **Filtrado Inteligente de Fuentes**
- **Problema:** El sistema mostraba todas las fuentes recuperadas, sin priorizar las más relevantes.
- **Solución:** Se diseñó una función `filter_most_relevant_sources` que:
  - Analiza palabras clave de la consulta y la respuesta.
  - Puntúa cada fuente según su relevancia.
  - Selecciona las 5 más relevantes de las 10 recuperadas.

### 3. **Mejoras en el Prompt del Sistema**
- **Problema:** El modelo citaba demasiadas fuentes o irrelevantes.
- **Solución:** Se actualizaron las instrucciones en `system_prompt.py` para:
  - Limitar las menciones a un máximo de 2 fuentes relevantes.
  - Priorizar fuentes oficiales y confiables.
  - Evitar citar fuentes innecesarias.

### 4. **Interfaz de Consola Mejorada**
- **Funcionalidad Existente:** El archivo `console_chat.py` ya proporcionaba una interfaz interactiva en consola.
- **Mejoras:**
  - Se verificó que el streaming de respuestas funcione correctamente.
  - Se limitó la visualización de fuentes a las 5 más relevantes.

---

## Requisitos Mínimos y Estado Actual

### 1. **Operación en Consola**
- ✅ Implementado con `console_chat.py`.
- Permite interacción en tiempo real con respuestas en streaming.

### 2. **Integración con API de Búsqueda**
- ✅ La API de búsqueda está integrada en `retrieval/search.py`.
- ⚠️ Pendiente: Finalizar el filtrado inteligente de fuentes.

### 3. **Streaming de Respuestas y Citación de Fuentes**
- ✅ Respuestas en streaming implementadas en `/api/chat/stream`.
- ✅ Fuentes citadas adecuadamente tras las mejoras en prompts y filtrado.

---

## Tareas Pendientes

1. **Finalizar Filtrado Inteligente de Fuentes**
   - Implementar y probar la función `filter_most_relevant_sources` en `chat_router.py`.

2. **Pruebas de Escenarios Clave**
   - Reformulación de consultas con pronombres (e.g., "¿Qué le puedo poner arriba?").
   - Preguntas sobre la conversación anterior (e.g., "¿De qué hablamos antes?").

3. **Actualizar Documentación**
   - Añadir ejemplos de uso y casos de prueba al README.
   - Documentar las nuevas funciones y mejoras implementadas.

---

## Plan de Trabajo Futuro

### 1. **Optimización del Sistema de Reformulación de Consultas**
- Implementar un sistema más robusto para detectar preguntas de seguimiento y reformularlas con el contexto necesario.
- Utilizar técnicas de procesamiento de lenguaje natural (NLP) para identificar referencias implícitas en las consultas.
- Realizar pruebas exhaustivas con diferentes escenarios conversacionales para garantizar la precisión.

### 2. **Mejoras en el Filtrado de Fuentes**
- Ajustar el algoritmo de puntuación para priorizar fuentes oficiales y confiables.
- Implementar un sistema de aprendizaje continuo que ajuste dinámicamente los criterios de relevancia según el historial de consultas.

### 3. **Ampliación de la Base de Conocimiento**
- Integrar más datos en la base de conocimiento para responder preguntas sin necesidad de búsquedas web.
- Implementar un sistema de actualización automática para mantener la base de conocimiento actualizada.

### 4. **Pruebas y Validación**
- Diseñar casos de prueba adicionales para cubrir escenarios complejos y poco comunes.
- Realizar pruebas de carga para garantizar el rendimiento del sistema bajo alta demanda.

### 5. **Documentación y Ejemplos de Uso**
- Ampliar la documentación del proyecto con ejemplos detallados de uso.
- Crear tutoriales interactivos para nuevos usuarios.

### 6. **Integración con Nuevas Plataformas**
- Explorar la posibilidad de integrar el chatbot con plataformas como Slack, Microsoft Teams o WhatsApp.
- Desarrollar una API pública para facilitar la integración con aplicaciones de terceros.

### 7. **Mejoras en la Experiencia de Usuario**
- Implementar un sistema de retroalimentación para que los usuarios puedan calificar las respuestas.
- Añadir soporte para múltiples idiomas para ampliar el alcance del chatbot.

---

## Conclusión
Este proyecto ha avanzado significativamente hacia el cumplimiento de sus objetivos. Las mejoras implementadas han optimizado la reformulación de consultas, la citación de fuentes y la experiencia de usuario en consola. Con las tareas pendientes completadas, el chatbot estará completamente alineado con los requisitos mínimos y ofrecerá una experiencia conversacional robusta y eficiente.