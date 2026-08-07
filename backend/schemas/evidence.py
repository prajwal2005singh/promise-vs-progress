from datetime import datetime

from pydantic import BaseModel


class EvidenceCreate(BaseModel):

    project_id: int

    description: str

    image_url: str | None = None

    latitude: float

    longitude: float

    captured_at: datetime


class EvidenceResponse(EvidenceCreate):

    id: int

    uploaded_by: int

    status: str

    reviewed_by: int | None

    review_comment: str | None

    created_at: datetime

    updated_at: datetime

    class Config:
        from_attributes = True