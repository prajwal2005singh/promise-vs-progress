from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database.db import get_db
from services.project_service import (
    get_projects,
    get_project_by_id
)

router = APIRouter()


@router.get("/projects")
def read_projects(db: Session = Depends(get_db)):
    return get_projects(db)


@router.get("/projects/{project_id}")
def read_project(project_id: int, db: Session = Depends(get_db)):
    return get_project_by_id(db, project_id)