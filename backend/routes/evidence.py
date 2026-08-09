from fastapi import APIRouter, Depends, HTTPException
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
    EvidenceRejectRequest
)

from services.evidence_service import (
    create_evidence,
    get_all_evidence,
    get_evidence_by_id,
    get_approved_evidence_for_project,
    approve_evidence,
    reject_evidence
)

router = APIRouter(
    prefix="/evidence",
    tags=["Evidence"]
)


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
    "/",
    response_model=EvidenceResponse
)
def upload_evidence(
    evidence: EvidenceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_citizen)
):

    return create_evidence(
        db,
        evidence,
        current_user.id
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