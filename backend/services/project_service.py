from sqlalchemy.orm import Session

from models.project import Project


def get_projects(db: Session):
    return db.query(Project).all()


def get_project_by_id(db: Session, project_id: int):
    return (
        db.query(Project)
        .filter(Project.id == project_id)
        .first()
    )


def get_delayed_projects(db: Session):
    return (
        db.query(Project)
        .filter(Project.status == "DELAYED")
        .all()
    )


def get_project_summary(db: Session):
    total = db.query(Project).count()

    ongoing = (
        db.query(Project)
        .filter(Project.status == "ONGOING")
        .count()
    )

    completed = (
        db.query(Project)
        .filter(Project.status == "COMPLETED")
        .count()
    )

    delayed = (
        db.query(Project)
        .filter(Project.status == "DELAYED")
        .count()
    )

    return {
        "total_projects": total,
        "ongoing": ongoing,
        "completed": completed,
        "delayed": delayed,
    }