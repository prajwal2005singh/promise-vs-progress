from datetime import datetime

from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Float,
    Boolean,
    ForeignKey
)
from sqlalchemy.orm import relationship

from models.base import Base


class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String, nullable=False)

    description = Column(String, nullable=False)

    category = Column(String, nullable=False, default="Road")

    department = Column(String, nullable=False)

    mla_name = Column(String, nullable=True)

    constituency = Column(String, nullable=True)

    location_name = Column(String, nullable=False)

    latitude = Column(Float, nullable=False)

    longitude = Column(Float, nullable=False)

    budget = Column(Integer, nullable=True)

    status = Column(String, nullable=False, default="ONGOING")

    # 0-100. This is the actual "progress" half of the platform's name --
    # admin-set based on verified evidence and site inspections. Without
    # it there's no way to compare what was promised against what's
    # really been delivered, which is the whole point of the project.
    progress_percent = Column(Integer, nullable=False, default=0)

    expected_completion = Column(DateTime, nullable=True)

    start_date = Column(DateTime, nullable=True)

    created_by = Column(Integer, ForeignKey("users.id"))

    created_at = Column(DateTime, default=datetime.utcnow)

    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    archived = Column(Boolean, default=False)

    # -------------------------
    # Relationships
    # -------------------------

    admin = relationship("User")

    proposals = relationship(
        "ProjectProposal",
        back_populates="project"
    )

    evidences = relationship(
        "Evidence",
        back_populates="project"
    )

    observations = relationship(
        "Observation",
        back_populates="project"
    )
