from fastapi import FastAPI
from routes.projects import router as project_router
from routes.auth import router as auth_router

app = FastAPI(
    title = "Promise VS Progress",
    version = "1.0.0"
)

app.include_router(project_router)
app.include_router(auth_router)