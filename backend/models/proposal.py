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

    id = Column(Integer, primary_key=True, index=True)

    submitted_by = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False
    )

    title = Column(String, nullable=False)

    description = Column(String, nullable=False)

    category = Column(String, nullable=False, default="Road")

    latitude = Column(Float, nullable=False)

    longitude = Column(Float, nullable=False)

    estimated_budget = Column(Integer, nullable=True)

    duplicate_score = Column(Float, nullable=True)

    status = Column(
        String,
        nullable=False,
        default="PENDING"
    )

    submitted_at = Column(
        DateTime,
        default=datetime.utcnow
    )

    reviewed_by = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=True
    )

    reviewed_at = Column(
        DateTime,
        nullable=True
    )

    approved_project_id = Column(
        Integer,
        ForeignKey("projects.id"),
        nullable=True
    )

    # -------------------------
    # Relationships
    # -------------------------

    citizen = relationship(
        "User",
        foreign_keys=[submitted_by]
    )

    admin = relationship(
        "User",
        foreign_keys=[reviewed_by]
    )

    project = relationship(
        "Project",
        back_populates="proposals",
        uselist=False
    )