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

    # --- Automated verification pipeline (see services/verification_service.py) ---
    # Populated when evidence is submitted through POST /evidence/upload
    # (an actual photo, EXIF-checked and AI-scored). Left null for the
    # legacy POST /evidence/ path where a citizen supplies image_url
    # manually -- there's nothing to fingerprint or score in that case.

    # sha256 of the photo's normalized pixel content. Exact-match only
    # (not perceptual): catches the same file being resubmitted, doesn't
    # try to detect two different photos of the same event.
    image_fingerprint = Column(
        String,
        nullable=True,
        index=True
    )

    # Gemini's best-guess assessment of the photo, 0-1. A signal for
    # admins reviewing the queue, not a verification result on its own.
    activity_score = Column(
        Float,
        nullable=True
    )

    completion_percentage = Column(
        Integer,
        nullable=True
    )

    # JSON-encoded list of strings, e.g. '["excavator", "rebar", "workers"]'
    ai_objects = Column(
        String,
        nullable=True
    )

    ai_reason = Column(
        String,
        nullable=True
    )

    # How many distinct citizens have now reported this same project at
    # roughly the same place and time (GPS + 7-day window). Informational
    # for the admin queue -- it does not bypass human review.
    confirming_citizens = Column(
        Integer,
        nullable=True
    )

    # New Image Engine output. These fields describe only what is visible;
    # they are intentionally NOT a project-level progress percentage.
    ai_broad_stage = Column(String, nullable=True)
    ai_stage = Column(String, nullable=True)
    ai_stage_completion = Column(String, nullable=True)
    ai_confidence = Column(Float, nullable=True)
    ai_evidence = Column(String, nullable=True)
    ai_activities = Column(String, nullable=True)

    # Context/authenticity status populated by the Context Engine.
    context_status = Column(String, nullable=True)
    location_status = Column(String, nullable=True)
    time_status = Column(String, nullable=True)
    provenance_status = Column(String, nullable=True)
    distance_to_project_m = Column(Float, nullable=True)

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
    location_match_type = Column(
        String,
        nullable=True
    )

    capture_age_days = Column(
        Float,
        nullable=True
    )
    observation = relationship(
        "Observation",
        back_populates="evidence",
        uselist=False,
        cascade="all, delete-orphan"
    )
