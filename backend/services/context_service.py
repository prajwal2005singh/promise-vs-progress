"""
context_service.py — project/location/time authenticity checks.

This engine deliberately does NOT claim cryptographic proof of capture time or GPS.
It validates EXIF metadata against the selected project and records the result so that
a future trusted-capture mobile flow can strengthen provenance without changing the API.
"""

from __future__ import annotations

import math
import os
from datetime import datetime, timedelta,timezone

from models.project import Project

PROJECT_GEOFENCE_METERS = float(os.getenv("PROJECT_GEOFENCE_METERS", "250"))
FUTURE_SKEW_MINUTES = int(os.getenv("CAPTURE_FUTURE_SKEW_MINUTES", "5"))
STALE_DAYS = int(os.getenv("CAPTURE_STALE_DAYS", "30"))
def _as_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)
def haversine_meters(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    radius = 6_371_000.0
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return 2 * radius * math.atan2(math.sqrt(a), math.sqrt(1 - a))

def validate_project_context(
    project: Project,
    latitude: float,
    longitude: float,
    captured_at: datetime,
    received_at: datetime,
) -> dict:
    distance = haversine_meters(
        latitude,
        longitude,
        project.latitude,
        project.longitude,
    )

    location_status = "VERIFIED" if distance <= PROJECT_GEOFENCE_METERS else "OUTSIDE_PROJECT_GEOFENCE"

    now = received_at
    if captured_at > now + timedelta(minutes=FUTURE_SKEW_MINUTES):
        time_status = "FUTURE_TIMESTAMP"
    elif project.start_date and captured_at < _as_utc(project.start_date):
        time_status = "BEFORE_PROJECT_START"
    elif project.expected_completion and captured_at > _as_utc(project.expected_completion):
        time_status = "AFTER_EXPECTED_COMPLETION" 
    elif captured_at < now - timedelta(days=STALE_DAYS):
        time_status = "STALE_METADATA"
    else:
        time_status = "VERIFIED_METADATA"

    # EXIF cannot prove that a user did not modify metadata. Call this explicitly out.
    provenance_status = "UNVERIFIED_SOURCE_CAPTURE"

    overall = "VERIFIED" if location_status == "VERIFIED" and time_status == "VERIFIED_METADATA" else "REVIEW"

    return {
        "project_id": project.id,
        "distance_to_project_m": round(distance, 2),
        "geofence_m": PROJECT_GEOFENCE_METERS,
        "location_status": location_status,
        "time_status": time_status,
        "provenance_status": provenance_status,
        "captured_at": captured_at.isoformat(),
        "received_at": received_at.isoformat(),
        "overall_status": overall,
    }

def is_context_acceptable(context: dict) -> bool:
    """Hard gate used for official evidence upload."""
    return context["location_status"] == "VERIFIED" and context["time_status"] == "VERIFIED_METADATA"
