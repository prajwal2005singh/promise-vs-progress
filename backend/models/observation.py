from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import relationship

from models.base import Base


class Observation(Base):
    __tablename__ = "observations"
    __table_args__ = (UniqueConstraint("evidence_id", name="uq_observation_evidence"),)

    id = Column(Integer, primary_key=True)
    evidence_id = Column(Integer, ForeignKey("evidence.id"), nullable=False, unique=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, index=True)

    captured_at = Column(DateTime, nullable=False)
    received_at = Column(DateTime, nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    image_hash = Column(String, nullable=False, index=True)

    location_status = Column(String, nullable=False, default="REVIEW")
    time_status = Column(String, nullable=False, default="REVIEW")
    provenance_status = Column(String, nullable=False, default="UNVERIFIED_SOURCE_CAPTURE")
    context_status = Column(String, nullable=False, default="REVIEW")
    distance_to_project_m = Column(Float, nullable=True)
    location_match_type = Column(String, nullable=True)
    capture_age_days = Column(Float, nullable=True)

    broad_stage = Column(String, nullable=True)
    fine_stage = Column(String, nullable=True)
    stage_completion = Column(String, nullable=True)
    vision_confidence = Column(Float, nullable=True)
    vision_components = Column(Text, nullable=True)
    vision_activities = Column(Text, nullable=True)
    vision_evidence = Column(Text, nullable=True)
    vision_reason = Column(Text, nullable=True)
    vision_payload = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    evidence = relationship("Evidence", back_populates="observation")
    project = relationship("Project", back_populates="observations")
