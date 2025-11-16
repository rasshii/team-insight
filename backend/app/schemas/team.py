"""
チーム管理関連のPydanticスキーマ
"""

from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field
from app.models.team import TeamRole
from app.schemas.users import UserInfo


# チーム基本スキーマ
class TeamBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="チーム名")
    description: Optional[str] = Field(None, description="チームの説明")


class TeamCreate(TeamBase):
    """チーム作成スキーマ"""

    pass


class TeamUpdate(BaseModel):
    """チーム更新スキーマ"""

    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None


# チームメンバー関連スキーマ
class TeamMemberBase(BaseModel):
    user_id: int = Field(..., description="ユーザーID")
    role: TeamRole = Field(TeamRole.MEMBER, description="チーム内での役割")


class TeamMemberCreate(TeamMemberBase):
    """チームメンバー追加スキーマ"""

    pass


class TeamMemberUpdate(BaseModel):
    """チームメンバー更新スキーマ"""

    role: TeamRole = Field(..., description="チーム内での役割")


class TeamMemberInfo(BaseModel):
    """チームメンバー情報"""

    id: int
    user_id: int
    team_id: int
    role: str
    joined_at: datetime
    user: UserInfo

    class Config:
        from_attributes = True


class Team(TeamBase):
    """チーム情報"""

    id: int
    created_at: datetime
    updated_at: datetime
    members: List[TeamMemberInfo] = []

    class Config:
        from_attributes = True


class TeamWithStats(Team):
    """統計情報付きチーム情報"""

    member_count: int = Field(..., description="メンバー数")
    active_tasks_count: int = Field(0, description="アクティブなタスク数")
    completed_tasks_this_month: int = Field(0, description="今月完了したタスク数")
    efficiency_score: float = Field(0.0, description="効率性スコア（0-100）")

    class Config:
        from_attributes = True


# レスポンススキーマ
class TeamListResponse(BaseModel):
    """チーム一覧レスポンス"""

    teams: List[Team]
    total: int
    page: int
    page_size: int


class TeamCreateResponse(BaseModel):
    """チーム作成レスポンス"""

    success: bool
    data: Team
    message: str = "チームが作成されました"


class TeamUpdateResponse(BaseModel):
    """チーム更新レスポンス"""

    success: bool
    data: Team
    message: str = "チームが更新されました"


class TeamDeleteResponse(BaseModel):
    """チーム削除レスポンス"""

    success: bool
    message: str = "チームが削除されました"


class TeamMemberAddResponse(BaseModel):
    """チームメンバー追加レスポンス"""

    success: bool
    data: TeamMemberInfo
    message: str = "メンバーが追加されました"


class TeamMemberRemoveResponse(BaseModel):
    """チームメンバー削除レスポンス"""

    success: bool
    message: str = "メンバーが削除されました"
