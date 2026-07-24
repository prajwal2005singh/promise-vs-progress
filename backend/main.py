from fastapi import FastAPI
from routes.projects import router

app = FastAPI()

app.include_router(router)