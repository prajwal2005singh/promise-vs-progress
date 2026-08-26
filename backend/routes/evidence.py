import uuid
import os
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, Depends, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from database.db import get_db

from auth.dependencies import (
    get_current_admin,
    get_current_citizen
)

from models.user import User

from schemas.evidence import (
    EvidenceCreate,
    EvidenceResponse,
    EvidenceRejectRequest,
    EvidenceUploadResponse
)

from services.evidence_service import (
    create_evidence_from_upload,
    get_all_evidence,
    get_evidence_by_id,
    get_approved_evidence_for_project,
    approve_evidence,
    reject_evidence,
    auto_approve_evidence
)

from services import verification_service, context_service
from services.project_service import get_project_by_id

router = APIRouter(
    prefix="/evidence",
    tags=["Evidence"]
)

# Uploaded evidence photos live here and are served back at /uploads/evidence/...
# (mounted in main.py). Kept separate from /static, which holds the built
# React app, so the two never collide.
UPLOAD_DIR = Path(__file__).resolve().parent.parent / "uploads" / "evidence"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

AUTO_APPROVE_CONFIDENCE = float(os.getenv("PVP_AUTO_APPROVE_CONFIDENCE", "0.75"))


@router.get(
    "/project/{project_id}",
    response_model=list[EvidenceResponse]
)
def list_approved_evidence_for_project(
    project_id: int,
    db: Session = Depends(get_db)
):
    """
    Public: admin-verified evidence for a single project, for display on
    that project's page. No auth required -- this is the citizen-facing
    proof feed the whole platform is built around.
    """

    return get_approved_evidence_for_project(db, project_id)


@router.post(
    "/upload",
    response_model=EvidenceUploadResponse
)
def upload_evidence_photo(
    project_id: int = Form(...),
    description: str = Form(...),
    photo: UploadFile = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_citizen)
):
    """
    The primary citizen-facing path: an actual photo, not a manually typed
    URL/lat/long. Runs the same pipeline the standalone verification
    prototype used -- EXIF GPS/timestamp extraction, exact-duplicate
    fingerprint check, Gemini construction-progress scoring, and a
    same-event confirmation count -- then creates the Evidence row. High-confidence Image Engine results are
    auto-approved; uncertain results remain PENDING for admin review.
    """

    if photo is None:
        raise HTTPException(status_code=422, detail="A photo is required.")

    suffix = Path(photo.filename or "").suffix or ".jpg"
    saved_name = f"{uuid.uuid4().hex}{suffix}"
    saved_path = UPLOAD_DIR / saved_name

    with open(saved_path, "wb") as out_file:
        out_file.write(photo.file.read())

    project = get_project_by_id(db, project_id)
    if project is None:
        saved_path.unlink(missing_ok=True)
        raise HTTPException(status_code=404, detail="Project not found.")

    exif_data = verification_service.extract_gps_and_timestamp(str(saved_path))
    if exif_data["latitude"] is None or exif_data["longitude"] is None or exif_data["captured_at"] is None:
        saved_path.unlink(missing_ok=True)
        raise HTTPException(
            status_code=422,
            detail=(
                "GPS and capture timestamp are required. Use the original camera file "
                "with location services enabled; forwarded/messaging-app copies may strip EXIF."
            ),
        )

    fingerprint = verification_service.generate_fingerprint(str(saved_path))
    if verification_service.is_duplicate_fingerprint(db, fingerprint):
        saved_path.unlink(missing_ok=True)
        raise HTTPException(
            status_code=409,
            detail="This exact image has already been submitted. Upload a new photo of current progress.",
        )

    received_at = datetime.now(timezone.utc).replace(tzinfo=None)
    context = context_service.validate_project_context(
        project=project,
        latitude=exif_data["latitude"],
        longitude=exif_data["longitude"],
        captured_at=exif_data["captured_at"],
        received_at=received_at,
    )

    if not context_service.is_context_acceptable(context):
        saved_path.unlink(missing_ok=True)
        if context["location_status"] not in {"VERIFIED", "PROVISIONALLY_MATCHED", "POINT_FALLBACK_VERIFIED"}:
            detail = (
                f"Photo location could not be accepted for this project: {context['location_status']}; "
                f"distance to the project geometry/reference is {context['distance_to_project_m']} m "
                f"with an allowed geofence of {context['geofence_m']} m. "
                f"For long/linear projects, ask an administrator to estimate/register corridor geometry first."
            )
        elif context.get("time_status") not in {"VERIFIED_METADATA", "AFTER_EXPECTED_COMPLETION_WARNING"}:
            detail = f"Capture timestamp could not be verified for this project: {context['time_status']}."
        else:
            detail = f"Project context could not be accepted: {context.get('overall_status')}."
        raise HTTPException(status_code=422, detail=detail)

    ai_result = verification_service.score_construction_activity(str(saved_path))

    confirmation = verification_service.check_confirmation(
        db,
        project_id=project_id,
        latitude=exif_data["latitude"],
        longitude=exif_data["longitude"],
        captured_at=exif_data["captured_at"],
        uploaded_by=current_user.id,
    )

    image_url = f"/uploads/evidence/{saved_name}"

    evidence = create_evidence_from_upload(
        db,
        project_id=project_id,
        description=description,
        image_url=image_url,
        latitude=exif_data["latitude"],
        longitude=exif_data["longitude"],
        captured_at=exif_data["captured_at"],
        user_id=current_user.id,
        fingerprint=fingerprint,
        image_analysis=ai_result,
        confirmation=confirmation,
        context=context,
    )

    # Only uncertain Image Engine results go to the admin queue.
    # High-confidence, valid road-construction observations are approved
    # automatically. Low-confidence/non-road/failed analysis remains PENDING
    # for a human decision.
    image_confidence = ai_result.get("confidence")
    image_is_valid = (
        ai_result.get("is_road_construction") is True
        and bool(ai_result.get("stage"))
        and isinstance(image_confidence, (int, float))
    )
    if image_is_valid and float(image_confidence) >= AUTO_APPROVE_CONFIDENCE:
        evidence = auto_approve_evidence(
            db,
            evidence.id,
            reason=(
                f"Auto-approved by Image Engine: confidence {float(image_confidence):.2f} "
                f">= threshold {AUTO_APPROVE_CONFIDENCE:.2f}."
            ),
        )

    observation = getattr(evidence, "observation", None)

    return EvidenceUploadResponse(
        evidence=evidence,
        construction_visible=ai_result.get("is_road_construction", False),
        likely_active_site=bool(ai_result.get("is_road_construction") and ai_result.get("confidence", 0) and ai_result.get("confidence", 0) >= 0.5),
        matching_report_ids=confirmation["matching_report_ids"],
        observation=observation,
        context=context,
    )


@router.post(
    "/",
    response_model=EvidenceResponse
)
def upload_evidence(
    evidence: EvidenceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_citizen)
):
    """Deprecated manual path. Official evidence must come from /evidence/upload."""
    raise HTTPException(
        status_code=410,
        detail=(
            "Manual evidence submission is disabled. Upload the original camera photo "
            "through POST /evidence/upload so GPS, capture time, duplicate checks, "
            "project context, and the Image Engine can run."
        ),
    )


@router.get(
    "/",
    response_model=list[EvidenceResponse]
)
def list_evidence(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):

    return get_all_evidence(db)


@router.get(
    "/{evidence_id}",
    response_model=EvidenceResponse
)
def get_evidence(
    evidence_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):

    evidence = get_evidence_by_id(
        db,
        evidence_id
    )

    if evidence is None:
        raise HTTPException(
            status_code=404,
            detail="Evidence not found"
        )

    return evidence


@router.put(
    "/approve/{evidence_id}",
    response_model=EvidenceResponse
)
def approve(
    evidence_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):

    evidence = approve_evidence(
        db,
        evidence_id,
        current_user.id
    )

    if evidence is None:
        raise HTTPException(
            status_code=404,
            detail="Evidence not found"
        )

    return evidence


@router.put(
    "/reject/{evidence_id}",
    response_model=EvidenceResponse
)
def reject(
    evidence_id: int,
    payload: EvidenceRejectRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):

    evidence = reject_evidence(
        db,
        evidence_id,
        current_user.id,
        payload.reason
    )

    if evidence is None:
        raise HTTPException(
            status_code=404,
            detail="Evidence not found"
        )

    return evidence