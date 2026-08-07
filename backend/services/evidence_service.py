from sqlalchemy.orm import Session

from models.evidence import Evidence
from schemas.evidence import EvidenceCreate


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