from datetime import datetime

from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Float,
    ForeignKey
)

from sqlalchemy.orm import relationship

from models.base import Base


class ProjectProposal(Base):

    __tablename__ = "project_proposals"

    id = Column(Integer, primary_key=True)

    name = Column(String, nullable=False)

    description = Column(String, nullable=False)

    category = Column(String, nullable=False)

    location_name = Column(String, nullable=False)

    latitude = Column(Float, nullable=False)

    longitude = Column(Float, nullable=False)

    budget = Column(Integer, nullable=True)

    status = Column(
        String,
        default="PENDING"
    )

    submitted_by = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False
    )

    reviewed_by = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=True
    )

    review_comment = Column(
        String,
        nullable=True
    )

    created_project_id = Column(
        Integer,
        ForeignKey("projects.id"),
        nullable=True
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )

    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    citizen = relationship(
        "User",
        foreign_keys=[submitted_by]
    )

    admin = relationship(
        "User",
        foreign_keys=[reviewed_by]
    )

    project = relationship(
        "Project"
    )