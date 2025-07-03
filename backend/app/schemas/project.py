# backend/app/schemas/project.py

from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class ProjectBase(BaseModel):
    name: str
    description: Optional[str] = None
    project_key: str


class ProjectCreate(ProjectBase):
    backlog_id: int


class ProjectUpdate(ProjectBase):
    name: Optional[str] = None
    description: Optional[str] = None
    project_key: Optional[str] = None


class ProjectInDB(ProjectBase):
    id: int
    backlog_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class Project(ProjectInDB):
    """APIレスポンス用"""

    pass
