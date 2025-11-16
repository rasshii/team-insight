"""
ユーザー管理APIエンドポイント

管理者のみがアクセスできるユーザー管理機能を提供します。
ユーザーの一覧表示、詳細表示、ロールの割り当て・削除・更新などを行います。
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_

from app.api.deps import get_db_session
from app.models.user import User
from app.models.rbac import Role, UserRole
from app.models.team import TeamMember
from app.schemas.users import (
    UserListResponse,
    UserResponse,
    UserUpdate,
    UserRoleAssignmentRequest,
    UserRoleRemovalRequest,
    UserRoleUpdateRequest,
)
from app.core.security import get_current_active_user
from app.core.permissions import require_role, RoleType
from app.schemas.auth import UserRoleResponse, RoleResponse

router = APIRouter()


@router.get("/", response_model=UserListResponse)
@require_role([RoleType.ADMIN])
async def list_users(
    page: int = Query(1, ge=1, description="ページ番号"),
    per_page: int = Query(20, ge=1, le=100, description="1ページあたりの件数"),
    search: Optional[str] = Query(None, description="検索キーワード（名前、メールアドレス）"),
    role_id: Optional[int] = Query(None, description="ロールIDでフィルタ"),
    is_active: Optional[bool] = Query(None, description="アクティブ状態でフィルタ"),
    project_id: Optional[int] = Query(None, description="プロジェクトIDでフィルタ"),
    team_id: Optional[int] = Query(None, description="チームIDでフィルタ"),
    sort_by: Optional[str] = Query("created_at", description="ソートフィールド"),
    sort_order: Optional[str] = Query("desc", description="ソート順序（asc/desc）"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db_session),
):
    """
    ユーザー一覧を取得（管理者専用）

    システム内の全ユーザーをページネーション付きで取得します。
    検索、フィルタリング、ソート機能により、目的のユーザーを効率的に見つけることができます。
    ユーザー管理画面で使用されます。

    認証:
        - 認証必須（アクティブなユーザーのみ）
        - 権限: ADMINロールが必要

    処理フロー:
        1. ユーザーの権限を確認（デコレーターで自動実行）
        2. クエリパラメータに基づいてフィルタリング条件を構築
        3. ユーザー情報とロール情報をeager loadingで取得
        4. 検索、フィルタ、ソートを適用
        5. ページネーションを適用
        6. ユーザー一覧とページネーション情報を返却

    Args:
        page: ページ番号（1から開始、デフォルト: 1）
        per_page: 1ページあたりの件数（1-100、デフォルト: 20）
        search: 検索キーワード（名前、メールアドレス、ユーザーIDで部分一致検索）
        role_id: ロールIDでフィルタ（指定したロールを持つユーザーのみ取得）
        is_active: アクティブ状態でフィルタ（True: アクティブ、False: 非アクティブ）
        project_id: プロジェクトIDでフィルタ（指定したプロジェクトのメンバーのみ取得）
        team_id: チームIDでフィルタ（指定したチームのメンバーのみ取得）
        sort_by: ソートフィールド（デフォルト: "created_at"）
                使用可能なフィールド: id, name, email, created_at, updated_atなど
        sort_order: ソート順序（"asc": 昇順、"desc": 降順、デフォルト: "desc"）
        current_user: 現在のユーザー（依存性注入）
        db: データベースセッション（依存性注入）

    Returns:
        UserListResponse: ユーザー一覧とページネーション情報
        {
            "users": [
                {
                    "id": 1,
                    "backlog_id": "user123",
                    "email": "user@example.com",
                    "name": "山田太郎",
                    "user_id": "yamada",
                    "is_active": true,
                    "user_roles": [
                        {
                            "id": 1,
                            "role_id": 1,
                            "project_id": null,
                            "role": {
                                "id": 1,
                                "name": "ADMIN",
                                "description": "管理者"
                            }
                        }
                    ],
                    "created_at": "2025-01-01T00:00:00Z",
                    "updated_at": "2025-01-15T10:30:00Z"
                },
                ...
            ],
            "total": 50,
            "page": 1,
            "per_page": 20
        }

    Raises:
        HTTPException(403): 権限がない場合（管理者以外）

    Examples:
        リクエスト例1（基本的な一覧取得）:
            GET /api/v1/users/?page=1&per_page=20

        リクエスト例2（検索とフィルタ）:
            GET /api/v1/users/?search=yamada&is_active=true&role_id=1

        リクエスト例3（プロジェクトメンバーの一覧）:
            GET /api/v1/users/?project_id=1&sort_by=name&sort_order=asc

        レスポンス例:
            {
                "users": [
                    {
                        "id": 1,
                        "backlog_id": "user123",
                        "email": "yamada@example.com",
                        "name": "山田太郎",
                        "user_id": "yamada",
                        "is_active": true,
                        "user_roles": [
                            {
                                "id": 1,
                                "role_id": 1,
                                "project_id": null,
                                "role": {
                                    "id": 1,
                                    "name": "ADMIN",
                                    "description": "管理者"
                                }
                            }
                        ],
                        "created_at": "2025-01-01T00:00:00Z",
                        "updated_at": "2025-01-15T10:30:00Z"
                    }
                ],
                "total": 50,
                "page": 1,
                "per_page": 20
            }

    Note:
        - eager loadingを使用してN+1問題を回避しています
        - 検索は大文字小文字を区別しません（ILIKE使用）
        - 複数のフィルタ条件を組み合わせることができます
        - ソートフィールドが存在しない場合はデフォルト（created_at）が使用されます

    フィルタリング・検索:
        - search: 名前、メールアドレス、user_idで部分一致検索（OR条件）
        - role_id: 指定したロールを持つユーザーのみ
        - is_active: アクティブ/非アクティブユーザーのみ
        - project_id: 指定したプロジェクトのメンバーのみ
        - team_id: 指定したチームのメンバーのみ

    パフォーマンス最適化:
        - joinedload: ユーザーロール情報を一度に取得（N+1問題の回避）
        - インデックス: 検索フィールド（name, email, user_id）にはインデックスが設定されています
    """
    # クエリの構築
    query = db.query(User).options(joinedload(User.user_roles).joinedload(UserRole.role))

    # 検索条件の適用
    if search:
        query = query.filter(
            or_(User.name.ilike(f"%{search}%"), User.email.ilike(f"%{search}%"), User.user_id.ilike(f"%{search}%"))
        )

    # ロールフィルタ
    if role_id is not None:
        query = query.join(User.user_roles).filter(UserRole.role_id == role_id)

    # アクティブ状態フィルタ
    if is_active is not None:
        query = query.filter(User.is_active == is_active)

    # プロジェクトフィルタ
    if project_id is not None:
        query = query.join(User.projects).filter(User.projects.any(id=project_id))

    # チームフィルタ
    if team_id is not None:
        query = query.join(User.team_memberships).filter(TeamMember.team_id == team_id)

    # ソート処理
    if sort_by and hasattr(User, sort_by):
        order_column = getattr(User, sort_by)
        if sort_order == "desc":
            query = query.order_by(order_column.desc())
        else:
            query = query.order_by(order_column.asc())
    else:
        # デフォルトはcreated_atの降順
        query = query.order_by(User.created_at.desc())

    # 総数を取得
    total = query.count()

    # ページネーション
    offset = (page - 1) * per_page
    users = query.offset(offset).limit(per_page).all()

    # レスポンスの構築
    user_responses = []
    for user in users:
        user_roles = []
        for ur in user.user_roles:
            user_roles.append(
                UserRoleResponse(
                    id=ur.id,
                    role_id=ur.role_id,
                    project_id=ur.project_id,
                    role=RoleResponse(id=ur.role.id, name=ur.role.name, description=ur.role.description),
                )
            )

        user_responses.append(
            UserResponse(
                id=user.id,
                backlog_id=user.backlog_id,
                email=user.email,
                name=user.name,
                user_id=user.user_id,
                is_active=user.is_active,
                user_roles=user_roles,
                created_at=user.created_at,
                updated_at=user.updated_at,
            )
        )

    return UserListResponse(users=user_responses, total=total, page=page, per_page=per_page)


@router.get("/{user_id}", response_model=UserResponse)
@require_role([RoleType.ADMIN])
async def get_user(
    user_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db_session),
):
    """
    特定のユーザー情報を取得します（管理者のみ）
    """
    user = db.query(User).options(joinedload(User.user_roles).joinedload(UserRole.role)).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="ユーザーが見つかりません")

    # レスポンスの構築
    user_roles = []
    for ur in user.user_roles:
        user_roles.append(
            UserRoleResponse(
                id=ur.id,
                role_id=ur.role_id,
                project_id=ur.project_id,
                role=RoleResponse(id=ur.role.id, name=ur.role.name, description=ur.role.description),
            )
        )

    return UserResponse(
        id=user.id,
        backlog_id=user.backlog_id,
        email=user.email,
        name=user.name,
        user_id=user.user_id,
        is_active=user.is_active,
        user_roles=user_roles,
        created_at=user.created_at,
        updated_at=user.updated_at,
    )


@router.patch("/{user_id}", response_model=UserResponse)
@require_role([RoleType.ADMIN])
async def update_user(
    user_id: int,
    user_update: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db_session),
):
    """
    ユーザー情報を更新します（管理者のみ）

    注意: ロールの変更は別のエンドポイントを使用してください
    """
    user = db.query(User).options(joinedload(User.user_roles).joinedload(UserRole.role)).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="ユーザーが見つかりません")

    # 更新可能なフィールドのみ更新
    update_data = user_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(user, field, value)

    db.commit()
    db.refresh(user)

    user_roles = []
    for ur in user.user_roles:
        user_roles.append(
            UserRoleResponse(
                id=ur.id,
                role_id=ur.role_id,
                project_id=ur.project_id,
                role=RoleResponse(id=ur.role.id, name=ur.role.name, description=ur.role.description),
            )
        )

    return UserResponse(
        id=user.id,
        backlog_id=user.backlog_id,
        email=user.email,
        name=user.name,
        user_id=user.user_id,
        is_active=user.is_active,
        user_roles=user_roles,
        created_at=user.created_at,
        updated_at=user.updated_at,
    )


@router.post("/{user_id}/roles", response_model=UserResponse)
@require_role([RoleType.ADMIN])
async def assign_roles(
    user_id: int,
    request: UserRoleAssignmentRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db_session),
):
    """
    ユーザーにロールを割り当て（管理者専用）

    指定したユーザーに1つまたは複数のロールを割り当てます。
    グローバルロール（全プロジェクト共通）とプロジェクト固有のロールの
    両方を割り当てることができます。RBAC権限管理の中核となる機能です。

    認証:
        - 認証必須（アクティブなユーザーのみ）
        - 権限: ADMINロールが必要

    処理フロー:
        1. ユーザーの権限を確認（デコレーターで自動実行）
        2. 対象ユーザーの存在を確認
        3. 各ロール割り当てについて:
           a. ロールの存在を確認
           b. 既存の割り当てがないかチェック
           c. 新規の場合のみUserRoleレコードを作成
        4. データベースにコミット
        5. 更新されたユーザー情報を返却

    Args:
        user_id: 対象ユーザーのID
        request: ロール割り当てリクエスト
                assignments: ロール割り当ての配列
                    - role_id: 割り当てるロールのID（必須）
                    - project_id: プロジェクトID（プロジェクト固有ロールの場合のみ、オプション）
        current_user: 現在のユーザー（依存性注入）
        db: データベースセッション（依存性注入）

    Returns:
        UserResponse: 更新されたユーザー情報（ロール情報を含む）
        {
            "id": 5,
            "backlog_id": "user123",
            "email": "user@example.com",
            "name": "佐藤次郎",
            "user_id": "sato",
            "is_active": true,
            "user_roles": [
                {
                    "id": 10,
                    "role_id": 2,
                    "project_id": null,
                    "role": {
                        "id": 2,
                        "name": "PROJECT_LEADER",
                        "description": "プロジェクトリーダー"
                    }
                },
                {
                    "id": 11,
                    "role_id": 3,
                    "project_id": 1,
                    "role": {
                        "id": 3,
                        "name": "MEMBER",
                        "description": "一般メンバー"
                    }
                }
            ],
            "created_at": "2025-01-01T00:00:00Z",
            "updated_at": "2025-01-15T10:30:00Z"
        }

    Raises:
        HTTPException(403): 権限がない場合（管理者以外）
        HTTPException(404): ユーザーまたはロールが見つからない場合
        HTTPException(400): 指定されたロールIDが無効な場合

    Examples:
        リクエスト例1（グローバルロールの割り当て）:
            POST /api/v1/users/5/roles
            Content-Type: application/json
            Cookie: auth_token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

            {
                "assignments": [
                    {
                        "role_id": 2,
                        "project_id": null
                    }
                ]
            }

        リクエスト例2（プロジェクト固有ロールの割り当て）:
            POST /api/v1/users/5/roles
            Content-Type: application/json

            {
                "assignments": [
                    {
                        "role_id": 3,
                        "project_id": 1
                    },
                    {
                        "role_id": 3,
                        "project_id": 2
                    }
                ]
            }

        リクエスト例3（複数ロールの同時割り当て）:
            POST /api/v1/users/5/roles
            Content-Type: application/json

            {
                "assignments": [
                    {
                        "role_id": 2,
                        "project_id": null
                    },
                    {
                        "role_id": 3,
                        "project_id": 1
                    }
                ]
            }

    Note:
        - 既に同じロールが割り当てられている場合はスキップされます（重複チェック）
        - グローバルロール: project_idがnullの場合、全プロジェクトに適用
        - プロジェクト固有ロール: project_idを指定すると、そのプロジェクトのみで有効
        - 複数のロールを一度に割り当てることができます
        - 割り当て後、すぐに権限が反映されます

    ロールの種類:
        - ADMIN: システム全体の管理者権限
        - PROJECT_LEADER: プロジェクトリーダー権限
        - MEMBER: 一般メンバー権限
        - VIEWER: 閲覧のみの権限

    RBAC権限管理:
        - ロールはpermissionsテーブルと連携して権限を管理
        - プロジェクト固有のロールは、そのプロジェクト内でのみ有効
        - グローバルロールはシステム全体で有効
    """
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="ユーザーが見つかりません")

    # 各ロール割り当てを処理
    for assignment in request.assignments:
        # ロールの存在確認
        role = db.query(Role).filter(Role.id == assignment.role_id).first()
        if not role:
            raise HTTPException(status_code=400, detail=f"ロールID {assignment.role_id} が見つかりません")

        # 既存の割り当てを確認
        existing = (
            db.query(UserRole)
            .filter(
                UserRole.user_id == user_id,
                UserRole.role_id == assignment.role_id,
                UserRole.project_id == assignment.project_id,
            )
            .first()
        )

        if not existing:
            # 新しいロール割り当てを作成
            user_role = UserRole(user_id=user_id, role_id=assignment.role_id, project_id=assignment.project_id)
            db.add(user_role)

    db.commit()

    # 更新されたユーザー情報を返す
    return await get_user(user_id, current_user, db)


@router.delete("/{user_id}/roles", response_model=UserResponse)
@require_role([RoleType.ADMIN])
async def remove_roles(
    user_id: int,
    request: UserRoleRemovalRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db_session),
):
    """
    ユーザーからロールを削除します（管理者のみ）
    """
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="ユーザーが見つかりません")

    # 各ユーザーロールを削除
    for user_role_id in request.user_role_ids:
        user_role = db.query(UserRole).filter(UserRole.id == user_role_id, UserRole.user_id == user_id).first()

        if user_role:
            db.delete(user_role)

    db.commit()

    # 更新されたユーザー情報を返す
    return await get_user(user_id, current_user, db)


@router.put("/{user_id}/roles", response_model=UserResponse)
@require_role([RoleType.ADMIN])
async def update_user_role(
    user_id: int,
    request: UserRoleUpdateRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db_session),
):
    """
    ユーザーのロールを更新します（管理者のみ）

    特定のユーザーロール割り当てのロールを変更します。
    """
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="ユーザーが見つかりません")

    # ユーザーロールを取得
    user_role = db.query(UserRole).filter(UserRole.id == request.user_role_id, UserRole.user_id == user_id).first()

    if not user_role:
        raise HTTPException(status_code=404, detail="ユーザーロール割り当てが見つかりません")

    # 新しいロールの存在確認
    new_role = db.query(Role).filter(Role.id == request.role_id).first()
    if not new_role:
        raise HTTPException(status_code=400, detail="指定されたロールが見つかりません")

    # ロールを更新
    user_role.role_id = request.role_id
    db.commit()

    # 更新されたユーザー情報を返す
    return await get_user(user_id, current_user, db)


@router.get("/roles/available", response_model=List[RoleResponse])
@require_role([RoleType.ADMIN])
async def get_available_roles(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db_session),
):
    """
    割り当て可能なロール一覧を取得します（管理者のみ）
    """
    roles = db.query(Role).all()

    return [RoleResponse(id=role.id, name=role.name, description=role.description) for role in roles]
