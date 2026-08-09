import logging

from sqlalchemy.orm import Session

from models.evidence import Evidence
from schemas.evidence import EvidenceCreate
from services.blockchain_service import anchor_evidence

log = logging.getLogger(__name__)


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