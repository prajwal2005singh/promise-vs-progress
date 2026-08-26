from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from auth.dependencies import get_current_admin
from database.db import get_db
from models.user import User
from schemas.project import ProjectResponse
from services.gis_service import GISServiceError, estimate_project_geometry, persist_estimated_geometry
from services.project_service import get_project_by_id

router = APIRouter(
    prefix="/projects",
    tags=["Project GIS"],
)


@router.post(
    "/{project_id}/geometry/estimate",
    response_model=ProjectResponse,
)
def estimate_geometry(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """
    Estimate a project's corridor from its metadata using:
        metadata parser -> geocoder -> road-network router -> validator.

    The resulting geometry is always marked ESTIMATED/REVIEW_REQUIRED and
    never pretends to be official geometry.
    """
    project = get_project_by_id(db, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found.")

    try:
        result = estimate_project_geometry(project)
    except GISServiceError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    if result.get("geometry") is None:
        raise HTTPException(
            status_code=422,
            detail={
                "message": "Could not estimate project geometry from current metadata.",
                "status": result.get("geometry_status"),
                "warnings": result.get("warnings", []),
            },
        )

    persist_estimated_geometry(project, result)
    db.commit()
    db.refresh(project)
    return project


@router.get(
    "/{project_id}/geometry",
)
def get_geometry(
    project_id: int,
    db: Session = Depends(get_db),
):
    project = get_project_by_id(db, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found.")

    return {
        "project_id": project.id,
        "name": project.name,
        "geometry": project.location_geometry,
        "status": project.location_geometry_status,
        "source": project.location_geometry_source,
        "confidence": project.location_geometry_confidence,
        "estimated_length_km": project.location_geometry_length_km,
        "metadata": project.location_geometry_metadata,
    }
