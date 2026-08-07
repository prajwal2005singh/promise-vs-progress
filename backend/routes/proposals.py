from fastapi import APIRouter, Depends, HTTPException

from sqlalchemy.orm import Session

from database.db import get_db

from auth.dependencies import (
    get_current_admin,
    get_current_citizen
)

from models.user import User

from schemas.proposal import (
    ProposalCreate,
    ProposalResponse
)

from services.proposal_service import (
    create_proposal,
    get_all_proposals,
    get_proposal_by_id,
    approve_proposal,
    reject_proposal
)

router = APIRouter(
    prefix="/proposals",
    tags=["Proposals"]
)


@router.post(
    "/",
    response_model=ProposalResponse
)
def submit_proposal(

    proposal: ProposalCreate,

    db: Session = Depends(get_db),

    current_user: User = Depends(get_current_citizen)

):

    return create_proposal(
        db,
        proposal,
        current_user.id
    )


@router.get(
    "/",
    response_model=list[ProposalResponse]
)
def list_proposals(

    db: Session = Depends(get_db),

    current_user: User = Depends(get_current_admin)

):

    return get_all_proposals(db)


@router.get(
    "/{proposal_id}",
    response_model=ProposalResponse
)
def get_proposal(

    proposal_id: int,

    db: Session = Depends(get_db),

    current_user: User = Depends(get_current_admin)

):

    proposal = get_proposal_by_id(
        db,
        proposal_id
    )

    if proposal is None:
        raise HTTPException(
            status_code=404,
            detail="Proposal not found"
        )

    return proposal


@router.put(
    "/approve/{proposal_id}",
    response_model=ProposalResponse
)
def approve(

    proposal_id: int,

    db: Session = Depends(get_db),

    current_user: User = Depends(get_current_admin)

):

    proposal = approve_proposal(
        db,
        proposal_id,
        current_user.id
    )

    if proposal is None:
        raise HTTPException(
            status_code=404,
            detail="Proposal not found"
        )

    return proposal


@router.put(
    "/reject/{proposal_id}",
    response_model=ProposalResponse
)
def reject(

    proposal_id: int,

    reason: str,

    db: Session = Depends(get_db),

    current_user: User = Depends(get_current_admin)

):

    proposal = reject_proposal(
        db,
        proposal_id,
        current_user.id,
        reason
    )

    if proposal is None:
        raise HTTPException(
            status_code=404,
            detail="Proposal not found"
        )

    return proposal