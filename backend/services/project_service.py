import json
import os

PROJECTS_FILE = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "data",
    "projects.json"
)

def load_projects():
    if not os.path.exists(PROJECTS_FILE):
        raise FileNotFoundError(
            "projects.json is not found. Run the scrapper.py first"
        )

    with open(PROJECTS_FILE, 'r', encoding="utf-8") as f:
        projects=json.load(f)

    return projects

def get_all_projects():
    return load_projects()

def get_delayed_projects():
    projects = load_projects()

    return [
        project
        for project in projects
        if project.get("status") == "Delayed"
    ]

def get_summary():

     projects = load_projects()
     return{
     "total": len(projects),
        "delayed": sum(
            1 for p in projects
            if p.get("status") == "Delayed"
        ),
        "on_track": sum(
            1 for p in projects
            if p.get("status") == "On Track"
        ),
        "unknown": sum(
            1 for p in projects
            if p.get("status") == "Unknown"
        ),
        "with_budget": sum(
            1 for p in projects
            if p.get("budget")
        ),
     }