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

    id = Column(Integer, primary_key=True)

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

    image_url = Column(
        String,
        nullable=True
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

    status = Column(
        String,
        default="PENDING"
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

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )

    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    project = relationship(
        "Project",
        back_populates="evidences"
    )

    uploader = relationship(
        "User",
        foreign_keys=[uploaded_by]
    )

    reviewer = relationship(
        "User",
        foreign_keys=[reviewed_by]
    )