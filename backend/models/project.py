from datetime import datetime

from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Float,
    Boolean,
    ForeignKey,
    JSON
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

    # Optional GeoJSON geometry for the full project footprint/corridor.
    # Road/tunnel projects should use LineString or MultiLineString;
    # city-wide/area programmes may use Polygon/MultiPolygon.
    location_geometry = Column(JSON, nullable=True)

    # Acceptance tolerance around the geometry, in metres.
    # If geometry is missing, the legacy latitude/longitude point is used
    # with this same tolerance and the result is marked POINT_FALLBACK.
    location_geofence_m = Column(Float, nullable=True)

    # GIS-estimated geometry metadata. These values are explicitly about
    # provenance/confidence; estimated geometry is never treated as official.
    location_geometry_status = Column(String, nullable=True)
    location_geometry_source = Column(String, nullable=True)
    location_geometry_confidence = Column(Float, nullable=True)
    location_geometry_length_km = Column(Float, nullable=True)
    location_geometry_metadata = Column(JSON, nullable=True)

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
    
