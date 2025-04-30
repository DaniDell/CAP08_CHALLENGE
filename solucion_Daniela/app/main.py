from fastapi import FastAPI

app = FastAPI(docs_url="/docs", redoc_url=None)  # Esto deshabilitará ReDoc pero mantendrá Swagger UI


from app.routers.chat_router import router as chat_router

app.include_router(chat_router, prefix="/api")