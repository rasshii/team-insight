"""
チーム管理APIエンドポイント
"""

from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.api import deps
from app.models.user import User
from app.models.team import TeamRole
from app.schemas.team import (
    Team,
    TeamWithStats,
    TeamCreate,
    TeamUpdate,
    TeamListResponse,
    TeamCreateResponse,
    TeamUpdateResponse,
    TeamDeleteResponse,
    TeamMemberCreate,
    TeamMemberUpdate,
    TeamMemberInfo,
    TeamMemberAddResponse,
    TeamMemberRemoveResponse
)
from app.services.team_service import team_service
from app.core.exceptions import (
    NotFoundException,
    ConflictException,
    ValidationException,
    PermissionDeniedException
)
from app.core.permissions import PermissionChecker, RoleType, require_role

router = APIRouter()


@router.get("/", response_model=TeamListResponse)
async def get_teams(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    with_stats: bool = Query(False),
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(get_db)
):
    """
    チーム一覧を取得
    
    - **page**: ページ番号（1以上）
    - **page_size**: ページサイズ（1-100）
    - **with_stats**: 統計情報を含むかどうか
    """
    skip = (page - 1) * page_size
    result = team_service.get_teams(
        db,
        skip=skip,
        limit=page_size,
        with_stats=with_stats
    )
    
    return TeamListResponse(
        teams=result["teams"],
        total=result["total"],
        page=page,
        page_size=page_size
    )


@router.get("/{team_id}", response_model=TeamWithStats)
async def get_team(
    team_id: int,
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(get_db)
):
    """
    チーム詳細を取得
    """
    try:
        return team_service.get_team(db, team_id, with_stats=True)
    except NotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.post("/", response_model=TeamCreateResponse)
@require_role([RoleType.PROJECT_LEADER, RoleType.ADMIN])
async def create_team(
    team_data: TeamCreate,
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(get_db)
):
    """
    チームを作成
    
    権限: PROJECT_LEADERまたはADMIN
    """
    try:
        team = team_service.create_team(db, team_data, current_user.id)
        return TeamCreateResponse(
            success=True,
            data=team
        )
    except ConflictException as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )


@router.put("/{team_id}", response_model=TeamUpdateResponse)
async def update_team(
    team_id: int,
    team_data: TeamUpdate,
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(get_db)
):
    """
    チームを更新
    
    権限: チームリーダーまたはADMIN
    """
    # チームリーダーかどうかを確認
    team = team_service.get_team(db, team_id, with_stats=False)
    is_team_leader = any(
        member.user_id == current_user.id and member.role == TeamRole.TEAM_LEADER
        for member in team.members
    )
    
    if not is_team_leader and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="チームの更新権限がありません"
        )
    
    try:
        team = team_service.update_team(db, team_id, team_data)
        return TeamUpdateResponse(
            success=True,
            data=team
        )
    except NotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except ConflictException as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )


@router.delete("/{team_id}", response_model=TeamDeleteResponse)
@require_role([RoleType.ADMIN])
async def delete_team(
    team_id: int,
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(get_db)
):
    """
    チームを削除
    
    権限: ADMINのみ
    """
    try:
        team_service.delete_team(db, team_id)
        return TeamDeleteResponse(success=True)
    except NotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.get("/{team_id}/members", response_model=list[TeamMemberInfo])
async def get_team_members(
    team_id: int,
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(get_db)
):
    """
    チームメンバー一覧を取得
    """
    try:
        team = team_service.get_team(db, team_id, with_stats=False)
        return team.members
    except NotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.post("/{team_id}/members", response_model=TeamMemberAddResponse)
async def add_team_member(
    team_id: int,
    member_data: TeamMemberCreate,
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(get_db)
):
    """
    チームにメンバーを追加
    
    権限: チームリーダーまたはADMIN
    """
    # チームリーダーかどうかを確認
    team = team_service.get_team(db, team_id, with_stats=False)
    is_team_leader = any(
        member.user_id == current_user.id and member.role == TeamRole.TEAM_LEADER
        for member in team.members
    )
    
    if not is_team_leader and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="メンバー追加権限がありません"
        )
    
    try:
        member = team_service.add_member(db, team_id, member_data)
        return TeamMemberAddResponse(
            success=True,
            data=member
        )
    except NotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except ConflictException as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )


@router.put("/{team_id}/members/{user_id}", response_model=TeamMemberInfo)
async def update_team_member(
    team_id: int,
    user_id: int,
    update_data: TeamMemberUpdate,
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(get_db)
):
    """
    チームメンバーの役割を更新
    
    権限: チームリーダーまたはADMIN
    """
    # チームリーダーかどうかを確認
    team = team_service.get_team(db, team_id, with_stats=False)
    is_team_leader = any(
        member.user_id == current_user.id and member.role == TeamRole.TEAM_LEADER
        for member in team.members
    )
    
    if not is_team_leader and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="メンバー更新権限がありません"
        )
    
    try:
        return team_service.update_member_role(
            db,
            team_id,
            user_id,
            update_data.role
        )
    except NotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.delete("/{team_id}/members/{user_id}", response_model=TeamMemberRemoveResponse)
async def remove_team_member(
    team_id: int,
    user_id: int,
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(get_db)
):
    """
    チームからメンバーを削除
    
    権限: チームリーダーまたはADMIN（自分自身の削除も可能）
    """
    # チームリーダーかどうかを確認
    team = team_service.get_team(db, team_id, with_stats=False)
    is_team_leader = any(
        member.user_id == current_user.id and member.role == TeamRole.TEAM_LEADER
        for member in team.members
    )
    
    # 自分自身を削除する場合、または管理権限がある場合のみ許可
    if user_id != current_user.id and not is_team_leader and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="メンバー削除権限がありません"
        )
    
    try:
        team_service.remove_member(db, team_id, user_id)
        return TeamMemberRemoveResponse(success=True)
    except NotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except ValidationException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/{team_id}/members/performance")
async def get_team_members_performance(
    team_id: int,
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(get_db)
):
    """
    チームメンバーのパフォーマンスデータを取得
    """
    try:
        team = team_service.get_team(db, team_id, with_stats=False)
        # メンバーのパフォーマンスデータを取得
        performance_data = team_service.get_members_performance(db, team_id)
        return performance_data
    except NotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.get("/{team_id}/task-distribution")
async def get_team_task_distribution(
    team_id: int,
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(get_db)
):
    """
    チームのタスク分配データを取得
    """
    try:
        team = team_service.get_team(db, team_id, with_stats=False)
        # タスク分配データを取得
        distribution_data = team_service.get_task_distribution(db, team_id)
        return distribution_data
    except NotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.get("/{team_id}/productivity-trend")
async def get_team_productivity_trend(
    team_id: int,
    period: str = Query("monthly", enum=["daily", "weekly", "monthly"]),
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(get_db)
):
    """
    チームの生産性推移データを取得
    """
    try:
        team = team_service.get_team(db, team_id, with_stats=False)
        # 生産性推移データを取得
        trend_data = team_service.get_productivity_trend(db, team_id, period)
        return trend_data
    except NotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.get("/{team_id}/activities")
async def get_team_activities(
    team_id: int,
    limit: int = Query(20, le=100),
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(get_db)
):
    """
    チームの最近のアクティビティを取得
    """
    try:
        team = team_service.get_team(db, team_id, with_stats=False)
        # アクティビティデータを取得
        activities = team_service.get_team_activities(db, team_id, limit)
        return activities
    except NotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )