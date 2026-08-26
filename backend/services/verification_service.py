"""
verification_service.py — Promise vs Progress
================================================
Automated checks run on a citizen's uploaded photo before it's queued for
admin review: does it actually have GPS + a timestamp, has this exact
image been submitted before, what does Gemini see in it, and how many
distinct citizens have now reported the same event.

Ported from the standalone `citizen-verification/verification` prototype
service into this backend, with two deliberate changes:
  - storage.py's in-memory dict is replaced by querying the real
    `Evidence` table (Postgres/SQLite via SQLAlchemy), so results survive
    a restart and match what admins already see in the review queue.
  - none of this blocks or auto-approves evidence. The prototype wrote
    straight to the chain once MIN_CONFIRMATIONS was hit; here, every
    submission still lands as PENDING and goes through the existing
    admin approve/reject flow (services/evidence_service.py). The AI
    score and confirmation count are surfaced to the citizen and the
    admin as a signal, not a verdict -- the Image Engine only describes the visible construction stage; it does not calculate project progress.
"""

import hashlib
import json
import logging
import os
from datetime import datetime, timedelta

from dotenv import load_dotenv
from PIL import Image
from PIL.ExifTags import GPSTAGS, TAGS
from sqlalchemy.orm import Session

from models.evidence import Evidence

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

# How close two reports need to be to count as confirming the SAME
# on-ground event, rather than being two unrelated uploads.
GPS_PROXIMITY_DEGREES = 0.001  # roughly 100m at Karnataka's latitude
TIME_WINDOW = timedelta(days=7)

# Fixed resolution every image is normalized to before fingerprinting, so
# two copies of the same photo at different sizes/qualities still collide.
FINGERPRINT_SIZE = (512, 512)

GEMINI_MODEL =  "gemini-3.5-flash-lite" #os.getenv("GEMINI_VERIFICATION_MODEL", "gemini-2.5-flash")


# ── EXIF: GPS + capture time ────────────────────────────────────────────

def extract_gps_and_timestamp(image_path: str) -> dict:
    """
    Pulls GPS coordinates and the capture timestamp out of a photo's EXIF
    data. A lot of phones strip GPS tags if location access was off when
    the photo was taken (and messaging apps strip EXIF entirely), so
    every field here can come back None -- callers handle that, this
    never raises.
    """
    result = {"latitude": None, "longitude": None, "captured_at": None}

    try:
        image = Image.open(image_path)
        exif_raw = image._getexif()
    except Exception as exc:
        log.warning("Could not read EXIF from %s: %s", image_path, exc)
        return result

    if not exif_raw:
        return result

    exif = {TAGS.get(tag, tag): value for tag, value in exif_raw.items()}

    if "DateTimeOriginal" in exif:
        try:
            result["captured_at"] = datetime.strptime(exif["DateTimeOriginal"], "%Y:%m:%d %H:%M:%S")
        except ValueError:
            pass

    gps_info = exif.get("GPSInfo")
    if gps_info:
        gps = {GPSTAGS.get(t, t): v for t, v in gps_info.items()}
        lat = _to_degrees(gps.get("GPSLatitude"))
        lon = _to_degrees(gps.get("GPSLongitude"))

        if lat is not None and gps.get("GPSLatitudeRef") == "S":
            lat = -lat
        if lon is not None and gps.get("GPSLongitudeRef") == "W":
            lon = -lon

        result["latitude"] = lat
        result["longitude"] = lon

    return result


def _to_degrees(dms) -> float | None:
    if not dms:
        return None
    degrees, minutes, seconds = dms
    return float(degrees) + float(minutes) / 60 + float(seconds) / 3600


# ── Exact-duplicate fingerprint ─────────────────────────────────────────

def generate_fingerprint(image_path: str) -> str:
    """
    64-char hex fingerprint of an image's pixel content only -- not its
    filename, EXIF, GPS, or camera model. Intentionally exact-match, not
    perceptual: two different photos of the same site should still get
    different fingerprints. Only a genuine re-upload of the same digital
    file should ever collide.
    """
    with Image.open(image_path) as image:
        normalized = image.resize(FINGERPRINT_SIZE).convert("RGB")
        pixel_bytes = normalized.tobytes()

    return hashlib.sha256(pixel_bytes).hexdigest()


def is_duplicate_fingerprint(db: Session, fingerprint: str) -> bool:
    """Has this exact image ever been submitted before, on any project?"""
    return (
        db.query(Evidence)
        .filter(Evidence.image_fingerprint == fingerprint)
        .first()
        is not None
    )


# ── Gemini construction-progress assessment ─────────────────────────────

def score_construction_activity(image_path: str) -> dict:
    """Backward-compatible wrapper around the new Image Engine.

    This function intentionally returns NO project-level progress percentage.
    """
    from services.image_engine import image_engine
    return image_engine.analyze(image_path)


# ── Multi-citizen confirmation ──────────────────────────────────────────

def check_confirmation(
    db: Session,
    project_id: int,
    latitude: float,
    longitude: float,
    captured_at: datetime,
    uploaded_by: int,
) -> dict:
    """
    Finds prior evidence on the same project that looks like the same
    on-ground event (close GPS, within a week) and counts how many
    DIFFERENT citizens have now reported it. One person uploading three
    photos of the same pothole shouldn't count as three confirmations.
    """
    candidates = (
        db.query(Evidence)
        .filter(Evidence.project_id == project_id)
        .all()
    )

    matching = [
        e for e in candidates
        if abs(e.latitude - latitude) <= GPS_PROXIMITY_DEGREES
        and abs(e.longitude - longitude) <= GPS_PROXIMITY_DEGREES
        and abs(e.captured_at - captured_at) <= TIME_WINDOW
    ]

    confirming_users = {e.uploaded_by for e in matching} | {uploaded_by}

    return {
        "matching_report_ids": [e.id for e in matching],
        "confirming_citizens": len(confirming_users),
    }


def encode_objects(objects: list[str] | None) -> str | None:
    """ai_objects is stored as a JSON string column; encode a list into one."""
    if objects is None:
        return None
    return json.dumps(objects)
