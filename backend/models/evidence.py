from datetime import datetime

from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    DateTime,
    ForeignKey
)
from sqlalchemy.orm import relationship

from models.base import Base


class Evidence(Base):
    __tablename__ = "evidence"

    id = Column(Integer, primary_key=True, index=True)

    project_id = Column(
        Integer,
        ForeignKey("projects.id"),
        nullable=False
    )

    uploaded_by = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False
    )

    description = Column(
        String,
        nullable=False
    )

    latitude = Column(
        Float,
        nullable=False
    )

    longitude = Column(
        Float,
        nullable=False
    )

    captured_at = Column(
        DateTime,
        nullable=False
    )

    uploaded_at = Column(
        DateTime,
        default=datetime.utcnow
    )

    trust_score = Column(
        Float,
        default=0
    )

    verification_status = Column(
        String,
        nullable=False,
        default="PENDING"
    )

    blockchain_status = Column(
        String,
        nullable=False,
        default="NOT_SENT"
    )

    # -------------------------
    # Relationships
    # -------------------------

    project = relationship(
        "Project",
        back_populates="evidences"
    )

    uploader = relationship(
        "User"
    )