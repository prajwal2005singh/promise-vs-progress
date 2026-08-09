from datetime import datetime
from typing import Optional


from pydantic import BaseModel


class ProjectBase(BaseModel):
    name: str
    description: str
    category: str
    department: str
    mla_name: Optional[str] = None
    constituency: Optional[str] = None
    location_name: str
    latitude: float
    longitude: float
    budget: Optional[int] = None
    status: str
    progress_percent: int = 0
    expected_completion: Optional[datetime] = None
    start_date: Optional[datetime] = None


class ProjectCreate(ProjectBase):
    pass


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    department: Optional[str] = None
    mla_name: Optional[str] = None
    constituency: Optional[str] = None
    location_name: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    budget: Optional[int] = None
    status: Optional[str] = None
    progress_percent: Optional[int] = None
    expected_completion: Optional[datetime] = None
    start_date: Optional[datetime] = None


class ProjectResponse(ProjectBase):
    id: int
    created_by: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    archived: bool

    class Config:
        from_attributes = True