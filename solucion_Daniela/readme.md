# Chatbot con FastAPI y LangChain

Este proyecto implementa un chatbot utilizando FastAPI y LangChain, con capacidad de búsqueda en Internet y manejo de base de conocimiento local.

## Estructura del Proyecto

```
├── app/                    # Núcleo de la aplicación
│   ├── config/            # Configuraciones y variables de entorno
│   ├── models/            # Modelos de datos
│   ├── routers/           # Endpoints de la API
│   ├── services/          # Servicios y lógica de negocio
│   └── utils/             # Utilidades y funciones auxiliares
├── data/                  # Almacenamiento de datos
├── prompt/                # Templates y prompts
├── retrieval/             # Módulos de búsqueda y recuperación
└── src/                   # Código fuente adicional
```

### Componentes Principales

#### 1. Configuración (`app/config/`)
- `settings.py`: Gestión de variables de entorno y configuraciones globales.

#### 2. API Endpoints (`app/routers/`)
- `chat_router.py`: Manejo de interacciones del chatbot
- `example_router.py`: Router de ejemplo y referencia

#### 3. Servicios (`app/services/`)
- `langchain_service.py`: Integración con LangChain
- `example_service.py`: Servicios de ejemplo

#### 4. Utilidades (`app/utils/`)
- `knowledge_base.py`: Gestión de la base de conocimiento
- `helpers.py`: Funciones auxiliares

#### 5. Búsqueda (`retrieval/`)
- `search.py`: Implementación de búsqueda en Internet

## Implementación Actual

### Base de Conocimiento
Actualmente implementada usando almacenamiento JSON:
- Ubicación: `data/knowledge_base.json`
- Gestión: `app/utils/knowledge_base.py`
- Características:
  - Almacenamiento simple y eficiente para desarrollo
  - Fácil mantenimiento y depuración
  - Persistencia de datos en archivo

### Búsqueda y Recuperación
- Integración con Google Custom Search API
- Procesamiento y almacenamiento de resultados
- Evita duplicados automáticamente

## Planes Futuros

### Implementación de Redis (Futura Mejora)
La estructura actual está preparada para migrar a Redis cuando sea necesario:

#### Beneficios Planificados
- Mejora en rendimiento con acceso en memoria
- Mayor escalabilidad
- Capacidad de caché
- Persistencia configurable

#### Configuración Preparada
```python
REDIS_URL = redis://localhost:6379  # Configurado en variables de entorno
```

#### Plan de Migración
1. **Fase 1: Preparación**
   - Instalación de Redis Server
   - Configuración de persistencia
   - Establecimiento de políticas de memoria

2. **Fase 2: Implementación**
   - Migración de datos JSON a Redis
   - Implementación de sistema de caché
   - Configuración de tiempo de expiración

3. **Fase 3: Validación**
   - Pruebas de rendimiento
   - Verificación de integridad
   - Validación de recuperación

## Requisitos

```bash
# Instalar dependencias
pip install -r requirements.txt
```

## Configuración

1. Crear archivo `.env` en la raíz del proyecto:
```env
GOOGLE_API_KEY=tu_clave
GOOGLE_CX=tu_cx
OPENAI_API_KEY=tu_clave
```

2. Asegurar permisos de escritura en `data/`

## Uso

```bash
# Iniciar el servidor
uvicorn app.main:app --reload
```

## Documentación API

Accede a la documentación interactiva en:
- Swagger UI: `http://localhost:8000/docs`

## Contribución

1. Fork el repositorio
2. Crea una rama para tu feature
3. Commit tus cambios
4. Push a la rama
5. Crea un Pull Request

## Licencia

Este proyecto está bajo la Licencia MIT.