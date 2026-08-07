from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from auth.dependencies import get_current_admin
from models.user import User

from database.db import get_db
from schemas.project import (
    ProjectCreate,
    ProjectUpdate,
    ProjectResponse
)
from services.project_service import (
    get_projects,
    get_project_by_id,
    create_project,
    update_project,
    delete_project
)

router = APIRouter(
    prefix="/projects",
    tags=["Projects"]
)


@router.get(
    "/",
    response_model=list[ProjectResponse]
)
def read_projects(db: Session = Depends(get_db)):
    return get_projects(db)


@router.get(
    "/{project_id}",
    response_model=ProjectResponse
)
def read_project(
    project_id: int,
    db: Session = Depends(get_db)
):

    project = get_project_by_id(db, project_id)

    if not project:
        raise HTTPException(
            status_code=404,
            detail="Project not found"
        )

    return project


@router.post(
    "/",
    response_model=ProjectResponse,
    status_code=201
)
def create_new_project(
    project: ProjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):

    return create_project(db, project)


@router.put(
    "/{project_id}",
    response_model=ProjectResponse
)
def update_existing_project(
    project_id: int,
    project: ProjectUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):

    updated = update_project(
        db,
        project_id,
        project
    )

    if not updated:
        raise HTTPException(
            status_code=404,
            detail="Project not found"
        )

    return updated


@router.delete(
    "/{project_id}"
)
def delete_existing_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):

    deleted = delete_project(
        db,
        project_id
    )

    if not deleted:
        raise HTTPException(
            status_code=404,
            detail="Project not found"
        )

    return {
        "message": "Project deleted successfully"
    }