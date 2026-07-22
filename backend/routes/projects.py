from services.project_service import(
    get_all_projects,
    get_delayed_projects,
    get_summary,
)
from fastapi import APIRouter



router = APIRouter()

@router.get("/api/projects")
def read_projects():
    projects = get_all_projects()
    return {
        "total": len(projects),
        "projects": projects
    }

@router.get("/api/projects/delayed")
def read_delayed_projects():
    delayed = get_delayed_projects()
    return {
        "total": len(delayed),
        "projects": delayed

    }


@router.get("/api/projects/summary")
def read_summary():
    return get_summary()
    