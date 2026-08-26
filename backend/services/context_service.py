"""
Context / authenticity engine for project evidence.

Key idea:
    A road/tunnel project is not a point. When a project has a GeoJSON
    corridor/area in Project.location_geometry, GPS is validated against
    that geometry. The legacy latitude/longitude point is only a fallback.

Supported GeoJSON geometry types:
    Point
    LineString
    MultiLineString
    Polygon
    MultiPolygon
    GeometryCollection (recursively)

The engine also normalizes EXIF/project timestamps to a configured
project timezone before comparing them with the server UTC receipt time.
"""

from __future__ import annotations

import math
import os
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from models.project import Project

DEFAULT_GEOFENCE_METERS = float(os.getenv("PROJECT_GEOFENCE_METERS", "250"))
FUTURE_SKEW_MINUTES = int(os.getenv("CAPTURE_FUTURE_SKEW_MINUTES", "5"))
STALE_DAYS = int(os.getenv("CAPTURE_STALE_DAYS", "30"))
TIMEZONE_NAME = os.getenv("PVP_PROJECT_TIMEZONE", "Asia/Kolkata")
ALLOW_POINT_FALLBACK = os.getenv("PVP_ALLOW_POINT_FALLBACK", "true").lower() == "true"
ALLOW_PROVISIONAL_GEOMETRY = os.getenv("PVP_ALLOW_PROVISIONAL_GEOMETRY", "true").lower() == "true"
REQUIRE_CORRIDOR_GEOMETRY = os.getenv("PVP_REQUIRE_CORRIDOR_GEOMETRY", "true").lower() == "true"
LINEAR_CATEGORIES = {"road", "road infrastructure", "ring road", "tunnel", "elevated corridor", "expressway", "highway"}

try:
    PROJECT_TZ = ZoneInfo(TIMEZONE_NAME)
except Exception:
    PROJECT_TZ = ZoneInfo("Asia/Kolkata")


def haversine_meters(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    radius = 6_371_000.0
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return 2 * radius * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _to_local_xy(lat: float, lon: float, origin_lat: float, origin_lon: float) -> tuple[float, float]:
    """Approximate local ENU metres around origin; sufficient for project-scale geometry."""
    meters_per_deg_lat = 111_320.0
    meters_per_deg_lon = 111_320.0 * math.cos(math.radians(origin_lat))
    return (
        (lon - origin_lon) * meters_per_deg_lon,
        (lat - origin_lat) * meters_per_deg_lat,
    )


def _point_to_segment_distance_m(
    lat: float,
    lon: float,
    a_lat: float,
    a_lon: float,
    b_lat: float,
    b_lon: float,
) -> float:
    px, py = _to_local_xy(lat, lon, lat, lon)
    ax, ay = _to_local_xy(a_lat, a_lon, lat, lon)
    bx, by = _to_local_xy(b_lat, b_lon, lat, lon)

    vx = bx - ax
    vy = by - ay
    wx = px - ax
    wy = py - ay
    denom = vx * vx + vy * vy

    if denom == 0:
        return math.hypot(wx, wy)

    t = max(0.0, min(1.0, (wx * vx + wy * vy) / denom))
    cx = ax + t * vx
    cy = ay + t * vy
    return math.hypot(px - cx, py - cy)


def _point_in_ring(lat: float, lon: float, ring: list[list[float]]) -> bool:
    inside = False
    if len(ring) < 3:
        return False

    x = lon
    y = lat
    j = len(ring) - 1

    for i in range(len(ring)):
        xi, yi = ring[i][0], ring[i][1]
        xj, yj = ring[j][0], ring[j][1]
        intersects = ((yi > y) != (yj > y)) and (
            x < (xj - xi) * (y - yi) / ((yj - yi) or 1e-15) + xi
        )
        if intersects:
            inside = not inside
        j = i

    return inside


def _ring_distance_m(lat: float, lon: float, ring: list[list[float]]) -> float:
    if len(ring) < 2:
        return float("inf")
    best = float("inf")
    for i in range(len(ring) - 1):
        a = ring[i]
        b = ring[i + 1]
        best = min(best, _point_to_segment_distance_m(lat, lon, a[1], a[0], b[1], b[0]))
    return best


def _geometry_distance_m(lat: float, lon: float, geometry: dict | None) -> float | None:
    if not geometry:
        return None

    gtype = geometry.get("type")
    coords = geometry.get("coordinates")

    if gtype == "Point":
        return haversine_meters(lat, lon, coords[1], coords[0])

    if gtype == "LineString":
        if len(coords) < 2:
            return None
        return min(
            _point_to_segment_distance_m(
                lat, lon,
                a[1], a[0],
                b[1], b[0],
            )
            for a, b in zip(coords, coords[1:])
        )

    if gtype == "MultiLineString":
        distances = []
        for line in coords or []:
            distances.extend(
                [
                    _point_to_segment_distance_m(
                        lat, lon,
                        a[1], a[0],
                        b[1], b[0],
                    )
                    for a, b in zip(line, line[1:])
                ]
            )
        return min(distances) if distances else None

    if gtype == "Polygon":
        rings = coords or []
        if not rings:
            return None
        if _point_in_ring(lat, lon, rings[0]):
            # Check holes: a point inside a hole is outside the polygon.
            for hole in rings[1:]:
                if _point_in_ring(lat, lon, hole):
                    return _ring_distance_m(lat, lon, hole)
            return 0.0
        return min((_ring_distance_m(lat, lon, ring) for ring in rings), default=None)

    if gtype == "MultiPolygon":
        distances = []
        for polygon in coords or []:
            d = _geometry_distance_m(lat, lon, {"type": "Polygon", "coordinates": polygon})
            if d is not None:
                distances.append(d)
        return min(distances) if distances else None

    if gtype == "GeometryCollection":
        distances = []
        for child in geometry.get("geometries", []):
            d = _geometry_distance_m(lat, lon, child)
            if d is not None:
                distances.append(d)
        return min(distances) if distances else None

    return None


def _parse_project_geometry(project: Project) -> dict | None:
    geometry = getattr(project, "location_geometry", None)
    if geometry is None:
        return None
    if isinstance(geometry, dict):
        return geometry
    if isinstance(geometry, str):
        import json
        try:
            return json.loads(geometry)
        except json.JSONDecodeError:
            return None
    return None


def _ensure_utc_naive(dt: datetime) -> datetime:
    """Interpret naive timestamps as project-local time, then return naive UTC."""
    if dt.tzinfo is None:
        localized = dt.replace(tzinfo=PROJECT_TZ)
    else:
        localized = dt.astimezone(PROJECT_TZ)
    return localized.astimezone(timezone.utc).replace(tzinfo=None)


def _project_date_utc(dt: datetime | None) -> datetime | None:
    return _ensure_utc_naive(dt) if dt else None


def _received_to_utc_naive(dt: datetime) -> datetime:
    """The upload route supplies received_at as an explicit UTC timestamp with tzinfo removed."""
    if dt.tzinfo is None:
        return dt
    return dt.astimezone(timezone.utc).replace(tzinfo=None)


def validate_project_context(
    project: Project,
    latitude: float,
    longitude: float,
    captured_at: datetime,
    received_at: datetime,
) -> dict:
    geometry = _parse_project_geometry(project)
    configured_radius = getattr(project, "location_geofence_m", None)
    category = str(getattr(project, "category", "") or "").strip().lower()
    requires_geometry = REQUIRE_CORRIDOR_GEOMETRY and category in LINEAR_CATEGORIES
    geofence_m = float(configured_radius or DEFAULT_GEOFENCE_METERS)

    geometry_status = getattr(project, "location_geometry_status", None) or ""
    geometry_source = getattr(project, "location_geometry_source", None) or ""

    if geometry:
        distance = _geometry_distance_m(latitude, longitude, geometry)
        location_match_type = "PROJECT_GEOMETRY"
        if distance is None:
            location_status = "GEOMETRY_INVALID"
        elif distance > geofence_m:
            location_status = "OUTSIDE_PROJECT_CORRIDOR"
        elif geometry_status == "REVIEW_REQUIRED":
            location_status = "GEOMETRY_REVIEW_REQUIRED"
        elif geometry_source == "ROUTING_FROM_PROJECT_METADATA" or geometry_status == "ESTIMATED":
            location_status = "PROVISIONALLY_MATCHED"
        else:
            location_status = "VERIFIED"
    else:
        distance = haversine_meters(
            latitude,
            longitude,
            project.latitude,
            project.longitude,
        )
        location_match_type = "POINT_FALLBACK"
        if requires_geometry:
            location_status = "CORRIDOR_GEOMETRY_REQUIRED"
        else:
            location_status = "POINT_FALLBACK_VERIFIED" if distance <= geofence_m else "OUTSIDE_PROJECT_GEOFENCE"

    received_utc = _received_to_utc_naive(received_at)
    captured_utc = _ensure_utc_naive(captured_at)

    start_utc = _project_date_utc(project.start_date)
    completion_utc = _project_date_utc(project.expected_completion)

    age_seconds = (received_utc - captured_utc).total_seconds()
    age_days = max(0.0, age_seconds / 86_400.0)

    if captured_utc > received_utc + timedelta(minutes=FUTURE_SKEW_MINUTES):
        time_status = "FUTURE_TIMESTAMP"
    elif start_utc and captured_utc < start_utc:
        time_status = "BEFORE_PROJECT_START"
    elif age_days > STALE_DAYS:
        time_status = "STALE_METADATA"
    elif completion_utc and captured_utc > completion_utc:
        # A project can be delayed/extended, so this is a warning, not a hard failure.
        time_status = "AFTER_EXPECTED_COMPLETION_WARNING"
    else:
        time_status = "VERIFIED_METADATA"

    # EXIF alone cannot prove that metadata was not edited.
    provenance_status = "UNVERIFIED_SOURCE_CAPTURE"

    if geometry:
        if location_status == "VERIFIED":
            location_ok = True
            location_verification = "VERIFIED"
        elif location_status == "PROVISIONALLY_MATCHED":
            location_ok = ALLOW_PROVISIONAL_GEOMETRY
            location_verification = "PROVISIONAL"
        else:
            location_ok = False
            location_verification = "FAILED"
    else:
        location_ok = ALLOW_POINT_FALLBACK and location_status == "POINT_FALLBACK_VERIFIED"
        location_verification = "POINT_FALLBACK" if location_ok else "FAILED"

    time_ok = time_status in {"VERIFIED_METADATA", "AFTER_EXPECTED_COMPLETION_WARNING"}

    if location_ok and time_ok:
        overall = "VERIFIED" if location_verification == "VERIFIED" else "PROVISIONALLY_VERIFIED"
    else:
        overall = "REVIEW"

    return {
        "project_id": project.id,
        "distance_to_project_m": round(distance, 2) if distance is not None else None,
        "geofence_m": geofence_m,
        "location_match_type": location_match_type,
        "location_status": location_status,
        "location_verification": location_verification,
        "geometry_status": geometry_status or None,
        "geometry_source": geometry_source or None,
        "time_status": time_status,
        "capture_age_days": round(age_days, 3),
        "provenance_status": provenance_status,
        "captured_at": captured_at.isoformat(),
        "captured_at_utc": captured_utc.isoformat(),
        "received_at": received_at.isoformat(),
        "received_at_utc": received_utc.isoformat(),
        "project_timezone": TIMEZONE_NAME,
        "geometry_used": bool(geometry),
        "overall_status": overall,
    }


def is_context_acceptable(context: dict) -> bool:
    """Hard gate used for official evidence upload."""
    return context.get("overall_status") in {"VERIFIED", "PROVISIONALLY_VERIFIED"}
