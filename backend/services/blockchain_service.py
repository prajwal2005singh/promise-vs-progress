import logging

from sqlalchemy.orm import Session

from blockchain_client import blockchain_client
from models.blockchain import BlockchainRecord

log = logging.getLogger(__name__)


def anchor_evidence(
    db: Session,
    evidence,
    record_type: str = "EVIDENCE"
) -> BlockchainRecord:
    """
    Hash an Evidence row's content and anchor that hash on-chain, then
    store a local BlockchainRecord mirroring the transaction.

    Called automatically when a citizen uploads evidence (record_type
    EVIDENCE) and again when an admin approves it (record_type
    VERIFIED_PROGRESS) -- so the chain shows both "this was submitted"
    and "this was independently confirmed" as separate, timestamped facts.
    """

    # Hash the parts of the evidence that should be auditable later:
    # claim, image fingerprint, location/time metadata, context checks, and
    # Image Engine interpretation. Mutable review fields such as status and
    # reviewer comments remain outside this hash.
    fingerprint = "|".join([
        str(evidence.project_id),
        evidence.description,
        evidence.image_url or "",
        evidence.image_fingerprint or "",
        str(evidence.latitude),
        str(evidence.longitude),
        evidence.captured_at.isoformat(),
        evidence.location_status or "",
        evidence.time_status or "",
        evidence.provenance_status or "",
        evidence.ai_broad_stage or "",
        evidence.ai_stage or "",
        evidence.ai_stage_completion or "",
        str(evidence.ai_confidence) if evidence.ai_confidence is not None else "",
        evidence.ai_evidence or "",
    ])

    data_hash = blockchain_client.hash_text(fingerprint)

    record = BlockchainRecord(
        project_id=evidence.project_id,
        evidence_id=evidence.id,
        record_type=record_type,
        data_hash=data_hash,
        submitted_by=evidence.uploaded_by,
        status="PENDING"
    )

    db.add(record)
    db.commit()
    db.refresh(record)

    try:
        result = blockchain_client.anchor_record(
            project_id=evidence.project_id,
            reference_id=evidence.id,
            record_type=record_type,
            data_hash=data_hash
        )

        record.tx_hash = result["tx_hash"]
        record.block_number = result["block_number"]
        record.status = result["status"]

    except Exception as exc:
        # Don't let a chain/RPC hiccup break evidence upload or approval --
        # the record stays PENDING and can be retried (e.g. via a small
        # background job) rather than failing the citizen-facing request.
        log.error("Failed to anchor record on-chain: %s", exc)
        record.status = "FAILED"

    db.commit()
    db.refresh(record)

    return record


def get_records_for_project(db: Session, project_id: int) -> list[BlockchainRecord]:
    return (
        db.query(BlockchainRecord)
        .filter(BlockchainRecord.project_id == project_id)
        .order_by(BlockchainRecord.created_at.asc())
        .all()
    )


def verify_hash(db: Session, data_hash: str):
    """
    Check whether a hash was genuinely anchored on-chain (source of
    truth), and return the matching local record if we have one, so the
    caller can show the tx hash / block number alongside the result.
    """

    normalized = data_hash if data_hash.startswith("0x") else f"0x{data_hash}"

    anchored = blockchain_client.is_hash_anchored(normalized)

    record = (
        db.query(BlockchainRecord)
        .filter(BlockchainRecord.data_hash == normalized)
        .first()
    )

    return anchored, record
