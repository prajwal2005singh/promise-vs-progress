from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from auth.dependencies import get_current_admin
from database.db import get_db
from models.observation import Observation
from schemas.evidence import ObservationResponse
from models.user import User

router = APIRouter(prefix="/observations", tags=["Observations"])


@router.get("/{observation_id}", response_model=ObservationResponse)
def get_observation(
    observation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    observation = db.query(Observation).filter(Observation.id == observation_id).first()
    if observation is None:
        raise HTTPException(status_code=404, detail="Observation not found")
    return observation


@router.get("/project/{project_id}", response_model=list[ObservationResponse])
def list_project_observations(
    project_id: int,
    db: Session = Depends(get_db),
):
    return (
        db.query(Observation)
        .filter(Observation.project_id == project_id)
        .order_by(Observation.captured_at.asc())
        .all()
    )
