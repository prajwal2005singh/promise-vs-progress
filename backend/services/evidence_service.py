import json
import logging
from datetime import datetime

from sqlalchemy.orm import Session

from models.evidence import Evidence
from models.observation import Observation
from schemas.evidence import EvidenceCreate
from services.blockchain_service import anchor_evidence
from services.verification_service import encode_objects

log = logging.getLogger(__name__)


def create_evidence_from_upload(
    db: Session,
    project_id: int,
    description: str,
    image_url: str,
    latitude: float,
    longitude: float,
    captured_at: datetime,
    user_id: int,
    fingerprint: str,
    image_analysis: dict,
    confirmation: dict,
    context: dict,
) -> Evidence:
    """Create evidence plus its canonical Observation snapshot."""

    db_evidence = Evidence(
        project_id=project_id,
        uploaded_by=user_id,
        description=description,
        image_url=image_url,
        latitude=latitude,
        longitude=longitude,
        captured_at=captured_at,
        image_fingerprint=fingerprint,
        activity_score=(
            image_analysis.get("confidence")
            if image_analysis.get("is_road_construction")
            else None
        ),
        completion_percentage=None,
        ai_objects=encode_objects(image_analysis.get("visible_components")),
        ai_reason=image_analysis.get("reason"),
        confirming_citizens=confirmation.get("confirming_citizens"),
        ai_broad_stage=image_analysis.get("broad_stage"),
        ai_stage=image_analysis.get("stage"),
        ai_stage_completion=image_analysis.get("stage_completion"),
        ai_confidence=image_analysis.get("confidence"),
        ai_evidence=encode_objects(image_analysis.get("evidence")),
        ai_activities=encode_objects(image_analysis.get("visible_activities")),
        context_status=context.get("overall_status"),
        location_status=context.get("location_status"),
        time_status=context.get("time_status"),
        provenance_status=context.get("provenance_status"),
        distance_to_project_m=context.get("distance_to_project_m"),
        location_match_type=context.get("location_match_type"),
        capture_age_days=context.get("capture_age_days"),
    )

    db.add(db_evidence)
    db.flush()

    observation = Observation(
        evidence_id=db_evidence.id,
        project_id=project_id,
        captured_at=captured_at,
        received_at=datetime.fromisoformat(context["received_at"]),
        latitude=latitude,
        longitude=longitude,
        image_hash=fingerprint,
        location_status=context.get("location_status", "REVIEW"),
        time_status=context.get("time_status", "REVIEW"),
        provenance_status=context.get("provenance_status", "UNVERIFIED_SOURCE_CAPTURE"),
        context_status=context.get("overall_status", "REVIEW"),
        distance_to_project_m=context.get("distance_to_project_m"),
        location_match_type=context.get("location_match_type"),
        capture_age_days=context.get("capture_age_days"),
        broad_stage=image_analysis.get("broad_stage"),
        fine_stage=image_analysis.get("stage"),
        stage_completion=image_analysis.get("stage_completion"),
        vision_confidence=image_analysis.get("confidence"),
        vision_components=encode_objects(image_analysis.get("visible_components")),
        vision_activities=encode_objects(image_analysis.get("visible_activities")),
        vision_evidence=encode_objects(image_analysis.get("evidence")),
        vision_reason=image_analysis.get("reason"),
        vision_payload=json.dumps(image_analysis, ensure_ascii=False),
    )

    db.add(observation)
    db.commit()
    db.refresh(db_evidence)

    try:
        anchor_evidence(db, db_evidence, record_type="EVIDENCE")
    except Exception as exc:
        log.error("Could not anchor evidence #%s on-chain: %s", db_evidence.id, exc)

    return db_evidence


def create_evidence(
    db: Session,
    evidence: EvidenceCreate,
    user_id: int
):

    db_evidence = Evidence(
        **evidence.model_dump(),
        uploaded_by=user_id
    )

    db.add(db_evidence)
    db.commit()
    db.refresh(db_evidence)

    # Anchor the raw submission on-chain as an EVIDENCE record. Failure
    # here should never block the citizen's upload, so we swallow errors
    # after logging -- the evidence row is what matters most immediately,
    # and a PENDING/FAILED blockchain record can be retried later.
    try:
        anchor_evidence(db, db_evidence, record_type="EVIDENCE")
    except Exception as exc:
        log.error("Could not anchor evidence #%s on-chain: %s", db_evidence.id, exc)

    return db_evidence


def get_all_evidence(db: Session):

    return db.query(Evidence).all()


def get_approved_evidence_for_project(db: Session, project_id: int):
    """
    Public-facing evidence feed: APPROVED evidence only. Approval can be
    automatic when the Image Engine is sufficiently confident or manual
    when the Image Engine sends the observation to the review queue.
    PENDING and REJECTED evidence remain out of the public feed.
    """

    return (
        db.query(Evidence)
        .filter(
            Evidence.project_id == project_id,
            Evidence.status == "APPROVED"
        )
        .order_by(Evidence.captured_at.desc())
        .all()
    )


def get_evidence_by_id(
    db: Session,
    evidence_id: int
):

    return (
        db.query(Evidence)
        .filter(Evidence.id == evidence_id)
        .first()
    )


def approve_evidence(
    db: Session,
    evidence_id: int,
    admin_id: int
):

    evidence = get_evidence_by_id(
        db,
        evidence_id
    )

    if evidence is None:
        return None

    evidence.status = "APPROVED"
    evidence.reviewed_by = admin_id

    db.commit()
    db.refresh(evidence)

    # A second, distinct on-chain record: this evidence has now been
    # admin-verified, not just submitted. Keeping EVIDENCE and
    # VERIFIED_PROGRESS as separate chain entries preserves the full
    # history -- a citizen can see both "what was claimed" and
    # "when/whether it was confirmed" independently.
    try:
        anchor_evidence(db, evidence, record_type="VERIFIED_PROGRESS")
    except Exception as exc:
        log.error("Could not anchor approval of evidence #%s on-chain: %s", evidence.id, exc)

    return evidence



def auto_approve_evidence(
    db: Session,
    evidence_id: int,
    reason: str = "Auto-approved by Image Engine: high-confidence road-construction observation.",
):
    """Approve evidence automatically when the Image Engine is confident.

    This uses the same public APPROVED status as manual approval, but leaves
    reviewed_by null and records the automated decision in review_comment.
    A separate VERIFIED_PROGRESS blockchain record is created so the audit
    trail shows that the evidence was accepted automatically rather than by
    a human administrator.
    """
    evidence = get_evidence_by_id(db, evidence_id)
    if evidence is None:
        return None

    evidence.status = "APPROVED"
    evidence.reviewed_by = None
    evidence.review_comment = reason

    db.commit()
    db.refresh(evidence)

    try:
        anchor_evidence(db, evidence, record_type="VERIFIED_PROGRESS")
    except Exception as exc:
        log.error("Could not anchor auto-approval of evidence #%s on-chain: %s", evidence.id, exc)

    return evidence

def reject_evidence(
    db: Session,
    evidence_id: int,
    admin_id: int,
    reason: str
):

    evidence = get_evidence_by_id(
        db,
        evidence_id
    )

    if evidence is None:
        return None

    evidence.status = "REJECTED"
    evidence.reviewed_by = admin_id
    evidence.review_comment = reason

    db.commit()
    db.refresh(evidence)

    return evidence