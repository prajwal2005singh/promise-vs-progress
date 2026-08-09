from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class BlockchainRecordResponse(BaseModel):

    id: int

    project_id: int

    evidence_id: Optional[int]

    record_type: str

    data_hash: str

    tx_hash: Optional[str]

    block_number: Optional[int]

    contract_record_index: Optional[int]

    status: str

    submitted_by: Optional[int]

    created_at: datetime

    class Config:
        from_attributes = True


class VerifyHashRequest(BaseModel):

    data_hash: str


class VerifyHashResponse(BaseModel):

    data_hash: str

    anchored_on_chain: bool

    record: Optional[BlockchainRecordResponse] = None
