from datetime import datetime

from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    ForeignKey
)

from sqlalchemy.orm import relationship

from models.base import Base


class BlockchainRecord(Base):
    """
    Local mirror of a record anchored on the ProgressRegistry smart
    contract (see /blockchain/contracts/ProgressRegistry.sol).

    The chain itself is the source of truth for tamper-proofing, but
    querying a blockchain node for every page load is slow. This table
    lets the API answer "what's the audit trail for project X" or
    "has this evidence been anchored yet" from Postgres/SQLite, while
    still exposing the transaction hash so anyone can independently
    verify the record on-chain (e.g. via Polygonscan).
    """

    __tablename__ = "blockchain_records"

    id = Column(Integer, primary_key=True)

    project_id = Column(
        Integer,
        ForeignKey("projects.id"),
        nullable=False
    )

    evidence_id = Column(
        Integer,
        ForeignKey("evidence.id"),
        nullable=True
    )

    # Mirrors the RecordType enum in ProgressRegistry.sol:
    # EVIDENCE | VERIFIED_PROGRESS | AUDIT_UPDATE
    record_type = Column(
        String,
        nullable=False
    )

    # keccak256 hash of the underlying content, hex-encoded with 0x prefix.
    data_hash = Column(
        String,
        nullable=False,
        index=True
    )

    # On-chain transaction details, filled in once the anchor tx is mined.
    tx_hash = Column(
        String,
        nullable=True,
        unique=True
    )

    block_number = Column(
        Integer,
        nullable=True
    )

    contract_record_index = Column(
        Integer,
        nullable=True
    )

    # PENDING while the tx is broadcast but not yet mined, CONFIRMED once
    # mined, FAILED if the chain rejected it (e.g. out of gas, RPC down).
    status = Column(
        String,
        nullable=False,
        default="PENDING"
    )

    submitted_by = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=True
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )

    project = relationship("Project")
    evidence = relationship("Evidence")
    submitter = relationship("User")
