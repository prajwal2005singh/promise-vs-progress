from sqlalchemy.orm import Session

from models.project import Project
from schemas.project import ProjectCreate, ProjectUpdate


# -------------------------
# Read Operations
# -------------------------

def get_projects(db: Session):
    return db.query(Project).all()


def get_project_by_id(db: Session, project_id: int):
    return (
        db.query(Project)
        .filter(Project.id == project_id)
        .first()
    )


# -------------------------
# Create Operation
# -------------------------

def create_project(db: Session, project: ProjectCreate):

    db_project = Project(
        **project.model_dump()
    )

    db.add(db_project)

    db.commit()

    db.refresh(db_project)

    return db_project


# -------------------------
# Update Operation
# -------------------------

def update_project(
    db: Session,
    project_id: int,
    project: ProjectUpdate
):

    db_project = get_project_by_id(db, project_id)

    if not db_project:
        return None

    update_data = project.model_dump(
        exclude_unset=True
    )

    for key, value in update_data.items():
        setattr(db_project, key, value)

    db.commit()

    db.refresh(db_project)

    return db_project


# -------------------------
# Delete Operation
# -------------------------

def delete_project(
    db: Session,
    project_id: int
):

    db_project = get_project_by_id(db, project_id)

    if not db_project:
        return None

    db.delete(db_project)

    db.commit()

    return db_project