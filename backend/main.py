from fastapi import FastAPI
from routes.projects import router as project_router
from routes.auth import router as auth_router
from routes.proposals import router as proposal_router
from routes.evidence import router as evidence_router

app = FastAPI(
    title = "Promise VS Progress",
    version = "1.0.0"
)

app.include_router(project_router)
app.include_router(auth_router)
app.include_router(proposal_router)
app.include_router(evidence_router)