from datetime import datetime, timezone

from sqlalchemy.orm import Session

from models.observation import Observation
from models.project import Project

from services.progress_engine import (
    ScheduleInfo,
    calculate_project_progress,
)


def calculate_project_progress_for_project(
    db: Session,
    project_id: int,
) -> dict | None:

    project = (
        db.query(Project)
        .filter(Project.id == project_id)
        .first()
    )

    if project is None:
        return None

    observations = (
        db.query(Observation)
        .filter(
            Observation.project_id == project_id
        )
        .order_by(Observation.captured_at.asc())
        .all()
    )


    schedule = ScheduleInfo(
        planned_start=project.start_date,
        planned_completion=project.expected_completion,
        as_of=datetime.now(timezone.utc),
    )

    return calculate_project_progress(
        observations=observations,
        schedule=schedule,
    )
