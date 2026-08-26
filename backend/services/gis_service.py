"""
Project GIS / geometry estimation engine.

Responsibilities:
    1. Parse structured route information from existing project metadata.
    2. Geocode named places with OpenStreetMap Nominatim (or a configured
       compatible geocoder).
    3. Build an estimated project corridor with OSRM (or configured router).
    4. Compare estimated route length with the project's declared length.
    5. Persist the estimated GeoJSON and confidence on the Project row.

IMPORTANT:
    This engine NEVER invents coordinates itself.
    It extracts place names, then asks a geocoder for real coordinates.
    The resulting geometry is explicitly marked ESTIMATED, not VERIFIED.

Environment:
    PVP_GEOCODER_URL=https://nominatim.openstreetmap.org/search
    PVP_ROUTER_URL=https://router.project-osrm.org/route/v1/driving
    PVP_GIS_USER_AGENT=PromiseVsProgress/1.0 (contact@example.com)
    PVP_GIS_TIMEOUT_SECONDS=20
    PVP_GIS_NOMINATIM_DELAY_SECONDS=1.1
    PVP_GIS_DEFAULT_CITY=Bengaluru
    PVP_GIS_DEFAULT_REGION=Karnataka
    PVP_GIS_DEFAULT_COUNTRY=India
"""

from __future__ import annotations

import re
import time
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Any

import requests

from models.project import Project

GEOCODER_URL = "https://nominatim.openstreetmap.org/search"
ROUTER_URL = "https://router.project-osrm.org/route/v1/driving"
TIMEOUT_SECONDS = 20.0
NOMINATIM_DELAY_SECONDS = 1.1
DEFAULT_CITY = "Bengaluru"
DEFAULT_REGION = "Karnataka"
DEFAULT_COUNTRY = "India"


def _env(name: str, default: str) -> str:
    import os
    return os.getenv(name, default)


def _normalize_text(value: str) -> str:
    value = value.strip()
    value = re.sub(r"\s+", " ", value)
    value = value.strip(" ,.;:-")
    return value


def _context_query(place: str, project: Project) -> str:
    location_name = _normalize_text(place)
    city = _env("PVP_GIS_DEFAULT_CITY", DEFAULT_CITY)
    region = _env("PVP_GIS_DEFAULT_REGION", DEFAULT_REGION)
    country = _env("PVP_GIS_DEFAULT_COUNTRY", DEFAULT_COUNTRY)

    # Use the project's city-like location_name as weak context only when
    # the project explicitly names Bengaluru. We still append the default
    # region/country to avoid surprising results for generic road names.
    project_text = " ".join(
        [
            str(getattr(project, "location_name", "") or ""),
            str(getattr(project, "description", "") or ""),
        ]
    ).lower()

    if "bengaluru" in project_text or "bangalore" in project_text:
        return f"{location_name}, Bengaluru, Karnataka, India"

    return f"{location_name}, {city}, {region}, {country}"


@dataclass
class ParsedLocation:
    location_type: str
    start_place: str | None
    end_place: str | None
    waypoints: list[str]
    declared_length_km: float | None
    source_text: str


@dataclass
class GeocodedPlace:
    query: str
    display_name: str
    latitude: float
    longitude: float
    place_type: str | None
    osm_type: str | None
    osm_id: str | None


class GISServiceError(RuntimeError):
    pass


def extract_declared_length_km(text: str) -> float | None:
    match = re.search(
        r"(?<!\d)(\d+(?:\.\d+)?)\s*(?:km|kilometres?|kilometers?)\b",
        text,
        flags=re.IGNORECASE,
    )
    if not match:
        return None
    return float(match.group(1))


def _split_waypoints(raw: str) -> list[str]:
    raw = _normalize_text(raw)
    if not raw:
        return []

    raw = re.sub(r"\band\b", ",", raw, flags=re.IGNORECASE)
    parts = [
        _normalize_text(part)
        for part in raw.split(",")
    ]
    return [part for part in parts if part]


def parse_project_location(project: Project) -> ParsedLocation:
    location_name = _normalize_text(
        getattr(project, "location_name", "") or ""
    )
    description = _normalize_text(
        getattr(project, "description", "") or ""
    )
    source_text = location_name or description
    combined = f"{location_name}. {description}"

    declared_length = extract_declared_length_km(combined)

    # Multi-segment/citywide projects should not be reduced to one fabricated
    # corridor. These require segment registration later.
    generic_multi = re.search(
        r"\b(citywide|across\s+bengaluru|major\s+roads|multiple\s+roads|throughout\s+bengaluru)\b",
        combined,
        flags=re.IGNORECASE,
    )
    if generic_multi:
        return ParsedLocation(
            location_type="MULTI_SEGMENT",
            start_place=None,
            end_place=None,
            waypoints=[],
            declared_length_km=declared_length,
            source_text=source_text,
        )

    patterns = [
        # A to B via X and Y
        re.compile(
            r"^(?P<start>.+?)\s+(?:to|until)\s+(?P<end>.+?)\s+via\s+(?P<via>.+)$",
            re.IGNORECASE,
        ),
        # A via X and Y to B
        re.compile(
            r"^(?P<start>.+?)\s+via\s+(?P<via>.+?)\s+(?:to|until)\s+(?P<end>.+)$",
            re.IGNORECASE,
        ),
        # from A to B
        re.compile(
            r"^from\s+(?P<start>.+?)\s+(?:to|until)\s+(?P<end>.+)$",
            re.IGNORECASE,
        ),
        # A to B
        re.compile(
            r"^(?P<start>.+?)\s+(?:to|until|–|-|—)\s+(?P<end>.+)$",
            re.IGNORECASE,
        ),
        # description-like: connecting A and B
        re.compile(
            r"connecting\s+(?P<start>.+?)\s+and\s+(?P<end>.+?)(?:\.|,|\s+under\b|$)",
            re.IGNORECASE,
        ),
        # description-like: between A and B
        re.compile(
            r"between\s+(?P<start>.+?)\s+and\s+(?P<end>.+?)(?:\.|,|\s+integrated\b|\s+under\b|$)",
            re.IGNORECASE,
        ),
    ]

    candidate = location_name
    match = next((pattern.search(candidate) for pattern in patterns if pattern.search(candidate)), None)

    # If the short location_name did not work, try selected description phrases.
    if not match:
        for pattern in patterns:
            match = pattern.search(description)
            if match:
                break

    if not match:
        return ParsedLocation(
            location_type="POINT_OR_UNKNOWN",
            start_place=None,
            end_place=None,
            waypoints=[],
            declared_length_km=declared_length,
            source_text=source_text,
        )

    start = _normalize_text(match.group("start"))
    end = _normalize_text(match.group("end"))
    via = match.groupdict().get("via")
    waypoints = _split_waypoints(via or "")

    # Strip common leading connective words accidentally captured in regexes.
    start = re.sub(r"^(from|between)\s+", "", start, flags=re.IGNORECASE).strip()
    end = re.sub(r"^(to|until)\s+", "", end, flags=re.IGNORECASE).strip()

    return ParsedLocation(
        location_type="LINEAR_CORRIDOR",
        start_place=start or None,
        end_place=end or None,
        waypoints=waypoints,
        declared_length_km=declared_length,
        source_text=source_text,
    )


def _session() -> requests.Session:
    session = requests.Session()
    user_agent = _env(
        "PVP_GIS_USER_AGENT",
        "PromiseVsProgress/1.0 random9943@proton.me",
    )
    session.headers.update(
        {
            "User-Agent": user_agent,
            "Accept-Language": "en",
        }
    )
    return session


def geocode_place(
    place: str,
    project: Project,
    session: requests.Session | None = None,
) -> GeocodedPlace:
    session = session or _session()
    query = _context_query(place, project)
    url = _env("PVP_GEOCODER_URL", GEOCODER_URL)
    timeout = float(_env("PVP_GIS_TIMEOUT_SECONDS", str(TIMEOUT_SECONDS)))

    try:
        response = session.get(
            url,
            params={
                "q": query,
                "format": "jsonv2",
                "limit": 1,
                "addressdetails": 1,
            },
            timeout=timeout,
        )
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as exc:
        raise GISServiceError(f"Geocoder request failed for '{place}': {exc}") from exc
    except ValueError as exc:
        raise GISServiceError(f"Geocoder returned invalid JSON for '{place}'.") from exc

    if not data:
        raise GISServiceError(f"Could not geocode project place '{place}'.")

    item = data[0]
    try:
        latitude = float(item["lat"])
        longitude = float(item["lon"])
    except (KeyError, TypeError, ValueError) as exc:
        raise GISServiceError(f"Geocoder result for '{place}' has invalid coordinates.") from exc

    return GeocodedPlace(
        query=query,
        display_name=str(item.get("display_name", place)),
        latitude=latitude,
        longitude=longitude,
        place_type=item.get("type"),
        osm_type=item.get("osm_type"),
        osm_id=str(item.get("osm_id")) if item.get("osm_id") is not None else None,
    )


def route_places(
    places: list[GeocodedPlace],
    session: requests.Session | None = None,
) -> tuple[dict, float]:
    if len(places) < 2:
        raise GISServiceError("At least two geocoded places are required for routing.")

    session = session or _session()
    url = _env("PVP_ROUTER_URL", ROUTER_URL)
    timeout = float(_env("PVP_GIS_TIMEOUT_SECONDS", str(TIMEOUT_SECONDS)))

    coordinates = ";".join(
        f"{place.longitude:.7f},{place.latitude:.7f}"
        for place in places
    )

    try:
        response = session.get(
            f"{url}/{coordinates}",
            params={
                "overview": "full",
                "geometries": "geojson",
                "steps": "false",
            },
            timeout=timeout,
        )
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as exc:
        raise GISServiceError(f"Routing request failed: {exc}") from exc
    except ValueError as exc:
        raise GISServiceError("Routing service returned invalid JSON.") from exc

    if data.get("code") != "Ok" or not data.get("routes"):
        raise GISServiceError(
            f"Routing service could not build a route: {data.get('code', 'UNKNOWN')}"
        )

    route = data["routes"][0]
    geometry = route.get("geometry")
    distance_km = float(route.get("distance", 0.0)) / 1000.0

    if not geometry or geometry.get("type") != "LineString":
        raise GISServiceError("Routing result did not include a LineString geometry.")

    return geometry, distance_km


def _length_error_percent(declared: float | None, estimated: float | None) -> float | None:
    if not declared or not estimated:
        return None
    return abs(estimated - declared) / declared * 100.0


def _confidence(
    parsed: ParsedLocation,
    geocoded_count: int,
    route_count: int,
    length_error_percent: float | None,
) -> float:
    if parsed.location_type != "LINEAR_CORRIDOR":
        return 0.0

    if geocoded_count < 2 or route_count < 2:
        return 0.0

    score = 0.65

    if parsed.waypoints:
        score += 0.10

    if length_error_percent is None:
        score += 0.05
    elif length_error_percent <= 10:
        score += 0.20
    elif length_error_percent <= 25:
        score += 0.10
    elif length_error_percent <= 40:
        score -= 0.10
    else:
        score -= 0.25

    return max(0.0, min(0.95, score))


def estimate_project_geometry(project: Project) -> dict[str, Any]:
    parsed = parse_project_location(project)

    base = {
        "project_id": project.id,
        "project_name": project.name,
        "location_type": parsed.location_type,
        "source_text": parsed.source_text,
        "declared_length_km": parsed.declared_length_km,
        "start_place": parsed.start_place,
        "end_place": parsed.end_place,
        "waypoints": parsed.waypoints,
        "geometry": None,
        "geometry_status": "UNKNOWN",
        "geometry_source": None,
        "geometry_confidence": 0.0,
        "estimated_length_km": None,
        "length_error_percent": None,
        "geocoded_places": [],
        "warnings": [],
    }

    if parsed.location_type == "MULTI_SEGMENT":
        base["geometry_status"] = "SEGMENT_REGISTRATION_REQUIRED"
        base["geometry_source"] = "PROJECT_METADATA"
        base["warnings"].append(
            "Project describes multiple road segments/area-wide work; a single corridor would be misleading."
        )
        return base

    if parsed.location_type != "LINEAR_CORRIDOR" or not parsed.start_place or not parsed.end_place:
        base["geometry_status"] = "INSUFFICIENT_LOCATION_DATA"
        base["geometry_source"] = "PROJECT_METADATA"
        base["warnings"].append(
            "Could not reliably extract a start/end corridor from the project metadata."
        )
        return base

    places = [parsed.start_place, *parsed.waypoints, parsed.end_place]
    session = _session()
    geocoded: list[GeocodedPlace] = []

    delay = float(
        _env(
            "PVP_GIS_NOMINATIM_DELAY_SECONDS",
            str(NOMINATIM_DELAY_SECONDS),
        )
    )

    for index, place in enumerate(places):
        try:
            result = geocode_place(place, project, session=session)
            geocoded.append(result)
            base["geocoded_places"].append(asdict(result))
        except GISServiceError as exc:
            base["warnings"].append(str(exc))
            return base

        if index < len(places) - 1:
            time.sleep(delay)

    try:
        geometry, estimated_length_km = route_places(
            geocoded,
            session=session,
        )
    except GISServiceError as exc:
        base["warnings"].append(str(exc))
        return base

    length_error = _length_error_percent(
        parsed.declared_length_km,
        estimated_length_km,
    )

    confidence = _confidence(
        parsed,
        len(geocoded),
        len(places),
        length_error,
    )

    status = "ESTIMATED"
    if length_error is not None and length_error > 40:
        status = "REVIEW_REQUIRED"
        base["warnings"].append(
            "Estimated road-network length differs from declared project length by more than 40%."
        )

    base.update(
        {
            "geometry": geometry,
            "geometry_status": status,
            "geometry_source": "ROUTING_FROM_PROJECT_METADATA",
            "geometry_confidence": round(confidence, 3),
            "estimated_length_km": round(estimated_length_km, 3),
            "length_error_percent": round(length_error, 2) if length_error is not None else None,
        }
    )

    return base


def persist_estimated_geometry(project: Project, result: dict[str, Any]) -> Project:
    """Persist only estimated geometry metadata; never mark it VERIFIED."""
    geometry = result.get("geometry")

    project.location_geometry = geometry
    project.location_geometry_status = result.get("geometry_status")
    project.location_geometry_source = result.get("geometry_source")
    project.location_geometry_confidence = result.get("geometry_confidence")
    project.location_geometry_length_km = result.get("estimated_length_km")
    project.location_geometry_metadata = {
        "estimated_at": datetime.utcnow().isoformat(),
        "declared_length_km": result.get("declared_length_km"),
        "length_error_percent": result.get("length_error_percent"),
        "start_place": result.get("start_place"),
        "end_place": result.get("end_place"),
        "waypoints": result.get("waypoints", []),
        "geocoded_places": result.get("geocoded_places", []),
        "warnings": result.get("warnings", []),
    }
    return project
