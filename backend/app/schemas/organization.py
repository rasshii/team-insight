"""
組織 / 組織メンバーシップの Pydantic スキーマ (Phase 0)
"""

import re
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


_SLUG_PATTERN = re.compile(r"^[a-z][a-z0-9-]{1,48}[a-z0-9]$")


class OrganizationBase(BaseModel):
    """組織の共通フィールド"""

    name: str = Field(..., min_length=1, max_length=100, description="組織名")
    slug: str = Field(..., min_length=3, max_length=50, description="組織 slug (英小文字+ハイフン)")
    fiscal_year_start_month: int = Field(
        4, ge=1, le=12, description="年度開始月 (1-12)"
    )
    timezone: str = Field("Asia/Tokyo", max_length=50, description="組織のタイムゾーン")
    settings: Dict[str, Any] = Field(default_factory=dict, description="組織別設定 (JSONB)")

    @field_validator("slug")
    @classmethod
    def _validate_slug(cls, value: str) -> str:
        if not _SLUG_PATTERN.match(value):
            raise ValueError(
                "slug は小文字英字で始まり、英小文字・数字・ハイフンのみ使用可能です"
            )
        return value


class OrganizationCreate(OrganizationBase):
    """組織作成リクエスト (System Admin のみ)"""


class OrganizationUpdate(BaseModel):
    """組織更新リクエスト (System Admin or Org Admin、フィールドは部分更新)"""

    name: Optional[str] = Field(None, min_length=1, max_length=100)
    fiscal_year_start_month: Optional[int] = Field(None, ge=1, le=12)
    timezone: Optional[str] = Field(None, max_length=50)
    settings: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


class OrganizationResponse(BaseModel):
    """組織レスポンス"""

    id: int
    name: str
    slug: str
    fiscal_year_start_month: int
    timezone: str
    settings: Dict[str, Any]
    is_active: bool
    deleted_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class OrganizationMemberCreate(BaseModel):
    """組織メンバー追加 (Org Admin)"""

    user_id: int = Field(..., description="追加するユーザー ID")
    role: str = Field(
        "MEMBER",
        description="組織内ロール (ADMIN / PROJECT_LEADER / MEMBER)",
    )

    @field_validator("role")
    @classmethod
    def _validate_role(cls, value: str) -> str:
        valid_roles = {"ADMIN", "PROJECT_LEADER", "MEMBER"}
        if value not in valid_roles:
            raise ValueError(f"role は {valid_roles} のいずれかである必要があります")
        return value


class OrganizationMemberUpdate(BaseModel):
    """組織メンバーロール変更 (Org Admin)"""

    role: str

    @field_validator("role")
    @classmethod
    def _validate_role(cls, value: str) -> str:
        valid_roles = {"ADMIN", "PROJECT_LEADER", "MEMBER"}
        if value not in valid_roles:
            raise ValueError(f"role は {valid_roles} のいずれかである必要があります")
        return value


class OrganizationMemberResponse(BaseModel):
    """組織メンバーシップレスポンス"""

    id: int
    organization_id: int
    user_id: int
    user_email: Optional[str] = None
    user_name: Optional[str] = None
    role: str
    joined_at: datetime

    model_config = ConfigDict(from_attributes=True)


class OrganizationListResponse(BaseModel):
    """組織一覧レスポンス"""

    items: List[OrganizationResponse]
    total: int
