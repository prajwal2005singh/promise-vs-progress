from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from auth.dependencies import get_current_admin
from database.db import get_db
from models.user import User

from services.project_progress_service import (
    calculate_project_progress_for_project,
)

router = APIRouter(
    prefix="/projects",
    tags=["Project Progress"],
)


@router.get("/{project_id}/progress")
def get_project_progress(
    project_id: int,
    db: Session = Depends(get_db),
):
    result = calculate_project_progress_for_project(
        db,
        project_id,
    )

    if result is None:
        raise HTTPException(
            status_code=404,
            detail="Project not found.",
        )

    return result
