from fastapi import FastAPI

app = FastAPI()


from app.routers.chat_router import router as chat_router

app.include_router(chat_router, prefix="/api")