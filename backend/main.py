from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import json, os

app = FastAPI(title="Promise vs Progress API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

PROJECTS_FILE = "projects.json"

@app.get("/")
def root():
    return {"message": "Promise vs Progress API is running!"}

@app.get("/api/projects")
def get_projects():
    if not os.path.exists(PROJECTS_FILE):
        return {"error": "projects.json not found. Run scraper.py first."}
    with open(PROJECTS_FILE, encoding="utf-8") as f:
        projects = json.load(f)
    return {"total": len(projects), "projects": projects}

@app.get("/api/projects/delayed")
def get_delayed():
    if not os.path.exists(PROJECTS_FILE):
        return {"error": "projects.json not found."}
    with open(PROJECTS_FILE, encoding="utf-8") as f:
        projects = json.load(f)
    delayed = [p for p in projects if p.get("status") == "Delayed"]
    return {"total": len(delayed), "projects": delayed}

@app.get("/api/projects/summary")
def get_summary():
    if not os.path.exists(PROJECTS_FILE):
        return {"error": "projects.json not found."}
    with open(PROJECTS_FILE, encoding="utf-8") as f:
        projects = json.load(f)
    summary = {
        "total":     len(projects),
        "delayed":   sum(1 for p in projects if p.get("status") == "Delayed"),
        "on_track":  sum(1 for p in projects if p.get("status") == "On Track"),
        "unknown":   sum(1 for p in projects if p.get("status") == "Unknown"),
        "with_budget": sum(1 for p in projects if p.get("budget")),
    }
    return summary