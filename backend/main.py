from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes.projects import router


app = FastAPI(title="Promise vs Progress API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(router)
PROJECTS_FILE = "projects.json"

@app.get("/")
def root():
    return{"message":"Promise VS Progress API is running sucessfully"}

