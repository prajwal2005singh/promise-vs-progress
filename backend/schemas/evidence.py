from __future__ import annotations

import json
from datetime import datetime

from pydantic import BaseModel, field_validator


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

    # --- automated verification pipeline, null on the legacy manual path ---
    image_fingerprint: str | None = None

    activity_score: float | None = None

    completion_percentage: int | None = None

    ai_objects: list[str] | None = None

    ai_reason: str | None = None

    confirming_citizens: int | None = None

    ai_broad_stage: str | None = None
    ai_stage: str | None = None
    ai_stage_completion: str | None = None
    ai_confidence: float | None = None
    ai_evidence: list[str] | None = None
    ai_activities: list[str] | None = None

    context_status: str | None = None
    location_status: str | None = None
    time_status: str | None = None
    provenance_status: str | None = None
    distance_to_project_m: float | None = None

    @field_validator("ai_objects", "ai_evidence", "ai_activities", mode="before")
    @classmethod
    def _parse_json_lists(cls, value):
        """JSON-encoded string columns are exposed as lists."""
        if value is None or isinstance(value, list):
            return value
        try:
            return json.loads(value)
        except (TypeError, ValueError):
            return None

    class Config:
        from_attributes = True


class EvidenceUploadResponse(BaseModel):
    """
    Returned by POST /evidence/upload. Wraps the created Evidence row with
    the AI assessment surfaced separately, so the citizen-facing UI can
    show "here's what the system saw" immediately without waiting on
    admin review.
    """

    evidence: EvidenceResponse

    construction_visible: bool

    likely_active_site: bool

    matching_report_ids: list[int]
    observation: ObservationResponse | None = None
    context: dict | None = None


class EvidenceRejectRequest(BaseModel):

    reason: str

class ObservationResponse(BaseModel):
    id: int
    evidence_id: int
    project_id: int
    captured_at: datetime
    received_at: datetime
    latitude: float
    longitude: float
    image_hash: str
    location_status: str
    time_status: str
    provenance_status: str
    context_status: str
    distance_to_project_m: float | None = None
    broad_stage: str | None = None
    fine_stage: str | None = None
    stage_completion: str | None = None
    vision_confidence: float | None = None
    vision_components: list[str] | None = None
    vision_activities: list[str] | None = None
    vision_evidence: list[str] | None = None
    vision_reason: str | None = None
    created_at: datetime

    @field_validator("vision_components", "vision_activities", "vision_evidence", mode="before")
    @classmethod
    def _parse_json_list(cls, value):
        if value is None or isinstance(value, list):
            return value
        try:
            return json.loads(value)
        except (TypeError, ValueError):
            return None

    class Config:
        from_attributes = True
