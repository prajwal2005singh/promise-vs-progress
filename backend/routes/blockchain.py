from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database.db import get_db

from auth.dependencies import get_current_admin

from models.user import User

from schemas.blockchain import (
    BlockchainRecordResponse,
    VerifyHashRequest,
    VerifyHashResponse
)

from services.blockchain_service import (
    get_records_for_project,
    verify_hash
)

router = APIRouter(
    prefix="/blockchain",
    tags=["Blockchain"]
)


@router.get(
    "/projects/{project_id}/records",
    response_model=list[BlockchainRecordResponse]
)
def list_project_records(
    project_id: int,
    db: Session = Depends(get_db)
):
    """
    Public audit trail for a project: every evidence submission,
    verified-progress confirmation, and status update that's been
    anchored on-chain, in chronological order.
    """

    return get_records_for_project(db, project_id)


@router.post(
    "/verify",
    response_model=VerifyHashResponse
)
def verify_data_hash(
    payload: VerifyHashRequest,
    db: Session = Depends(get_db)
):
    """
    Anyone -- a citizen, a journalist, an auditor -- can independently
    confirm that a given content hash was really anchored on-chain,
    without needing to trust this backend's database.
    """

    try:
        anchored, record = verify_hash(db, payload.data_hash)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))

    return VerifyHashResponse(
        data_hash=payload.data_hash,
        anchored_on_chain=anchored,
        record=record
    )
