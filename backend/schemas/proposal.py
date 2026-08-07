from datetime import datetime

from pydantic import BaseModel


class ProposalCreate(BaseModel):

    name: str

    description: str

    category: str

    location_name: str

    latitude: float

    longitude: float

    budget: int | None = None


class ProposalResponse(ProposalCreate):

    id: int

    status: str

    submitted_by: int

    reviewed_by: int | None

    review_comment: str | None

    created_project_id: int | None

    created_at: datetime

    updated_at: datetime

    class Config:
        from_attributes = True