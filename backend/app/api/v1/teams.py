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
    TeamMemberRemoveResponse,
)
from app.services.team_service import team_service
from app.core.exceptions import NotFoundException, ConflictException, ValidationException, PermissionDeniedException
from app.core.permissions import PermissionChecker, RoleType, require_role

router = APIRouter()


@router.get("/", response_model=TeamListResponse)
async def get_teams(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    with_stats: bool = Query(False),
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(get_db),
):
    """
    チーム一覧を取得

    システム内の全チームの一覧をページネーション付きで取得します。
    オプションで各チームの統計情報（メンバー数、アクティブタスク数など）も含めることができます。

    認証:
        - 認証必須（アクティブなユーザーのみ）

    処理フロー:
        1. ページ番号とページサイズからオフセットを計算
        2. team_serviceを使用してチーム一覧を取得
        3. 統計情報が要求された場合は、各チームの統計も取得
        4. ページネーション情報と共にレスポンスを返却

    Args:
        page: ページ番号（1から開始、デフォルト: 1）
        page_size: 1ページあたりの件数（1-100、デフォルト: 20）
        with_stats: 統計情報を含むかどうか（デフォルト: False）
        current_user: 現在のユーザー（依存性注入）
        db: データベースセッション（依存性注入）

    Returns:
        TeamListResponse: チーム一覧とページネーション情報
        {
            "teams": [
                {
                    "id": 1,
                    "name": "開発チーム",
                    "description": "バックエンド開発チーム",
                    "member_count": 5,
                    "active_tasks": 15,
                    "created_at": "2025-01-01T00:00:00",
                    "updated_at": "2025-01-15T10:30:00"
                },
                ...
            ],
            "total": 50,
            "page": 1,
            "page_size": 20
        }

    Examples:
        リクエスト例1（基本的な一覧取得）:
            GET /api/v1/teams/?page=1&page_size=20

        リクエスト例2（統計情報を含む）:
            GET /api/v1/teams/?page=1&page_size=20&with_stats=true

        レスポンス例:
            {
                "teams": [
                    {
                        "id": 1,
                        "name": "バックエンド開発チーム",
                        "description": "APIとデータベースの開発を担当",
                        "member_count": 5,
                        "active_tasks": 15,
                        "created_at": "2025-01-01T00:00:00Z",
                        "updated_at": "2025-01-15T10:30:00Z"
                    }
                ],
                "total": 50,
                "page": 1,
                "page_size": 20
            }

    Note:
        - ページ番号は1から開始します
        - ページサイズは最大100件まで指定可能です
        - with_statsをtrueにすると、各チームのメンバー数とアクティブタスク数が含まれます
        - 統計情報の取得には追加のクエリが必要なため、パフォーマンスに影響する可能性があります
    """
    skip = (page - 1) * page_size
    result = team_service.get_teams(db, skip=skip, limit=page_size, with_stats=with_stats)

    return TeamListResponse(teams=result["teams"], total=result["total"], page=page, page_size=page_size)


@router.get("/{team_id}", response_model=TeamWithStats)
async def get_team(team_id: int, current_user: User = Depends(deps.get_current_user), db: Session = Depends(get_db)):
    """
    チーム詳細を取得
    """
    try:
        return team_service.get_team(db, team_id, with_stats=True)
    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/", response_model=TeamCreateResponse)
@require_role([RoleType.PROJECT_LEADER, RoleType.ADMIN])
async def create_team(
    team_data: TeamCreate, current_user: User = Depends(deps.get_current_user), db: Session = Depends(get_db)
):
    """
    新しいチームを作成

    プロジェクトリーダーまたは管理者が新しいチームを作成します。
    チームを作成したユーザーは自動的にチームリーダーとして登録されます。

    認証:
        - 認証必須（アクティブなユーザーのみ）
        - 権限: PROJECT_LEADERまたはADMINロールが必要

    処理フロー:
        1. ユーザーの権限を確認（デコレーターで自動実行）
        2. team_serviceを使用してチームを作成
        3. 作成したユーザーをチームリーダーとして登録
        4. 作成されたチーム情報を返却

    Args:
        team_data: チーム作成データ
                  name: チーム名（必須）
                  description: チームの説明（任意）
        current_user: 現在のユーザー（依存性注入）
        db: データベースセッション（依存性注入）

    Returns:
        TeamCreateResponse: 作成されたチーム情報
        {
            "success": true,
            "data": {
                "id": 1,
                "name": "開発チーム",
                "description": "バックエンド開発チーム",
                "created_at": "2025-01-15T10:30:00",
                "updated_at": "2025-01-15T10:30:00",
                "members": [
                    {
                        "user_id": 1,
                        "user_name": "山田太郎",
                        "role": "TEAM_LEADER"
                    }
                ]
            }
        }

    Raises:
        HTTPException(403): 権限がない場合
        HTTPException(409): 同名のチームが既に存在する場合

    Examples:
        リクエスト例:
            POST /api/v1/teams/
            Content-Type: application/json
            Cookie: auth_token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

            {
                "name": "バックエンド開発チーム",
                "description": "APIとデータベースの開発を担当"
            }

        レスポンス例:
            {
                "success": true,
                "data": {
                    "id": 1,
                    "name": "バックエンド開発チーム",
                    "description": "APIとデータベースの開発を担当",
                    "created_at": "2025-01-15T10:30:00Z",
                    "updated_at": "2025-01-15T10:30:00Z",
                    "members": [
                        {
                            "user_id": 1,
                            "user_name": "山田太郎",
                            "role": "TEAM_LEADER"
                        }
                    ]
                }
            }

    Note:
        - チーム名は一意である必要があります
        - チームを作成したユーザーは自動的にチームリーダーになります
        - チームリーダーはメンバーの追加・削除、チーム情報の更新が可能です
    """
    try:
        team = team_service.create_team(db, team_data, current_user.id)
        return TeamCreateResponse(success=True, data=team)
    except ConflictException as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.put("/{team_id}", response_model=TeamUpdateResponse)
async def update_team(
    team_id: int, team_data: TeamUpdate, current_user: User = Depends(deps.get_current_user), db: Session = Depends(get_db)
):
    """
    チームを更新

    権限: チームリーダーまたはADMIN
    """
    # チームリーダーかどうかを確認
    team = team_service.get_team(db, team_id, with_stats=False)
    is_team_leader = any(member.user_id == current_user.id and member.role == TeamRole.TEAM_LEADER for member in team.members)

    if not is_team_leader and not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="チームの更新権限がありません")

    try:
        team = team_service.update_team(db, team_id, team_data)
        return TeamUpdateResponse(success=True, data=team)
    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ConflictException as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.delete("/{team_id}", response_model=TeamDeleteResponse)
@require_role([RoleType.ADMIN])
async def delete_team(team_id: int, current_user: User = Depends(deps.get_current_user), db: Session = Depends(get_db)):
    """
    チームを削除

    権限: ADMINのみ
    """
    try:
        team_service.delete_team(db, team_id)
        return TeamDeleteResponse(success=True)
    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/{team_id}/members", response_model=list[TeamMemberInfo])
async def get_team_members(team_id: int, current_user: User = Depends(deps.get_current_user), db: Session = Depends(get_db)):
    """
    チームメンバー一覧を取得
    """
    try:
        team = team_service.get_team(db, team_id, with_stats=False)
        return team.members
    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/{team_id}/members", response_model=TeamMemberAddResponse)
async def add_team_member(
    team_id: int,
    member_data: TeamMemberCreate,
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(get_db),
):
    """
    チームにメンバーを追加

    指定されたチームに新しいメンバーを追加します。
    追加するユーザーのロール（TEAM_LEADER または MEMBER）を指定できます。

    認証:
        - 認証必須（アクティブなユーザーのみ）
        - 権限: チームリーダーまたはADMINロールが必要

    処理フロー:
        1. チーム情報を取得
        2. 現在のユーザーがチームリーダーまたは管理者であることを確認
        3. 追加するユーザーの存在を確認
        4. team_serviceを使用してメンバーを追加
        5. 追加されたメンバー情報を返却

    Args:
        team_id: チームID
        member_data: メンバー追加データ
                    user_id: 追加するユーザーのID（必須）
                    role: メンバーのロール（TEAM_LEADER または MEMBER、デフォルト: MEMBER）
        current_user: 現在のユーザー（依存性注入）
        db: データベースセッション（依存性注入）

    Returns:
        TeamMemberAddResponse: 追加されたメンバー情報
        {
            "success": true,
            "data": {
                "user_id": 5,
                "user_name": "佐藤次郎",
                "email": "sato@example.com",
                "role": "MEMBER",
                "joined_at": "2025-01-15T10:30:00"
            }
        }

    Raises:
        HTTPException(403): 権限がない場合
        HTTPException(404): チームまたはユーザーが見つからない場合
        HTTPException(409): ユーザーが既にチームのメンバーである場合

    Examples:
        リクエスト例:
            POST /api/v1/teams/1/members
            Content-Type: application/json
            Cookie: auth_token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

            {
                "user_id": 5,
                "role": "MEMBER"
            }

        レスポンス例:
            {
                "success": true,
                "data": {
                    "user_id": 5,
                    "user_name": "佐藤次郎",
                    "email": "sato@example.com",
                    "role": "MEMBER",
                    "joined_at": "2025-01-15T10:30:00Z"
                }
            }

    Note:
        - チームには複数のチームリーダーを設定できます
        - 同じユーザーを重複して追加することはできません
        - メンバーを追加できるのは、チームリーダーまたは管理者のみです
    """
    # チームリーダーかどうかを確認
    team = team_service.get_team(db, team_id, with_stats=False)
    is_team_leader = any(member.user_id == current_user.id and member.role == TeamRole.TEAM_LEADER for member in team.members)

    if not is_team_leader and not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="メンバー追加権限がありません")

    try:
        member = team_service.add_member(db, team_id, member_data)
        return TeamMemberAddResponse(success=True, data=member)
    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ConflictException as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.put("/{team_id}/members/{user_id}", response_model=TeamMemberInfo)
async def update_team_member(
    team_id: int,
    user_id: int,
    update_data: TeamMemberUpdate,
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(get_db),
):
    """
    チームメンバーの役割を更新

    権限: チームリーダーまたはADMIN
    """
    # チームリーダーかどうかを確認
    team = team_service.get_team(db, team_id, with_stats=False)
    is_team_leader = any(member.user_id == current_user.id and member.role == TeamRole.TEAM_LEADER for member in team.members)

    if not is_team_leader and not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="メンバー更新権限がありません")

    try:
        return team_service.update_member_role(db, team_id, user_id, update_data.role)
    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.delete("/{team_id}/members/{user_id}", response_model=TeamMemberRemoveResponse)
async def remove_team_member(
    team_id: int, user_id: int, current_user: User = Depends(deps.get_current_user), db: Session = Depends(get_db)
):
    """
    チームからメンバーを削除

    権限: チームリーダーまたはADMIN（自分自身の削除も可能）
    """
    # チームリーダーかどうかを確認
    team = team_service.get_team(db, team_id, with_stats=False)
    is_team_leader = any(member.user_id == current_user.id and member.role == TeamRole.TEAM_LEADER for member in team.members)

    # 自分自身を削除する場合、または管理権限がある場合のみ許可
    if user_id != current_user.id and not is_team_leader and not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="メンバー削除権限がありません")

    try:
        team_service.remove_member(db, team_id, user_id)
        return TeamMemberRemoveResponse(success=True)
    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/{team_id}/members/performance")
async def get_team_members_performance(
    team_id: int, current_user: User = Depends(deps.get_current_user), db: Session = Depends(get_db)
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
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/{team_id}/task-distribution")
async def get_team_task_distribution(
    team_id: int, current_user: User = Depends(deps.get_current_user), db: Session = Depends(get_db)
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
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/{team_id}/productivity-trend")
async def get_team_productivity_trend(
    team_id: int,
    period: str = Query("monthly", enum=["daily", "weekly", "monthly"]),
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(get_db),
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
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/{team_id}/activities")
async def get_team_activities(
    team_id: int,
    limit: int = Query(20, le=100),
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(get_db),
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
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
