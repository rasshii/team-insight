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
    sort_by: Optional[str] = Query("created_at", description="ソートフィールド"),
    sort_order: Optional[str] = Query("desc", description="ソート順序（asc/desc）"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db_session),
):
    """
    ユーザー一覧を取得します（管理者のみ）
    
    - **page**: ページ番号（1から開始）
    - **per_page**: 1ページあたりの件数（最大100）
    - **search**: 名前またはメールアドレスで部分一致検索
    - **role_id**: 特定のロールを持つユーザーのみ取得
    - **is_active**: アクティブ/非アクティブでフィルタ
    """
    # クエリの構築
    query = db.query(User).options(
        joinedload(User.user_roles).joinedload(UserRole.role)
    )
    
    # 検索条件の適用
    if search:
        query = query.filter(
            or_(
                User.name.ilike(f"%{search}%"),
                User.email.ilike(f"%{search}%"),
                User.user_id.ilike(f"%{search}%")
            )
        )
    
    # ロールフィルタ
    if role_id is not None:
        query = query.join(User.user_roles).filter(UserRole.role_id == role_id)
    
    # アクティブ状態フィルタ
    if is_active is not None:
        query = query.filter(User.is_active == is_active)
    
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
            user_roles.append(UserRoleResponse(
                id=ur.id,
                role_id=ur.role_id,
                project_id=ur.project_id,
                role=RoleResponse(
                    id=ur.role.id,
                    name=ur.role.name,
                    description=ur.role.description
                )
            ))
        
        user_responses.append(UserResponse(
            id=user.id,
            backlog_id=user.backlog_id,
            email=user.email,
            name=user.name,
            user_id=user.user_id,
            is_active=user.is_active,
            user_roles=user_roles,
            created_at=user.created_at,
            updated_at=user.updated_at
        ))
    
    return UserListResponse(
        users=user_responses,
        total=total,
        page=page,
        per_page=per_page
    )


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
    user = db.query(User).options(
        joinedload(User.user_roles).joinedload(UserRole.role)
    ).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="ユーザーが見つかりません")
    
    # レスポンスの構築
    user_roles = []
    for ur in user.user_roles:
        user_roles.append(UserRoleResponse(
            id=ur.id,
            role_id=ur.role_id,
            project_id=ur.project_id,
            role=RoleResponse(
                id=ur.role.id,
                name=ur.role.name,
                description=ur.role.description
            )
        ))
    
    return UserResponse(
        id=user.id,
        backlog_id=user.backlog_id,
        email=user.email,
        name=user.name,
        user_id=user.user_id,
        is_active=user.is_active,
        user_roles=user_roles,
        created_at=user.created_at,
        updated_at=user.updated_at
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
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="ユーザーが見つかりません")
    
    # 更新可能なフィールドのみ更新
    update_data = user_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(user, field, value)
    
    db.commit()
    db.refresh(user)
    
    # ロール情報を含めて返す
    user = db.query(User).options(
        joinedload(User.user_roles).joinedload(UserRole.role)
    ).filter(User.id == user_id).first()
    
    user_roles = []
    for ur in user.user_roles:
        user_roles.append(UserRoleResponse(
            id=ur.id,
            role_id=ur.role_id,
            project_id=ur.project_id,
            role=RoleResponse(
                id=ur.role.id,
                name=ur.role.name,
                description=ur.role.description
            )
        ))
    
    return UserResponse(
        id=user.id,
        backlog_id=user.backlog_id,
        email=user.email,
        name=user.name,
        user_id=user.user_id,
        is_active=user.is_active,
        user_roles=user_roles,
        created_at=user.created_at,
        updated_at=user.updated_at
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
    ユーザーにロールを割り当てます（管理者のみ）
    
    既に同じロールが割り当てられている場合はスキップされます。
    """
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="ユーザーが見つかりません")
    
    # 各ロール割り当てを処理
    for assignment in request.assignments:
        # ロールの存在確認
        role = db.query(Role).filter(Role.id == assignment.role_id).first()
        if not role:
            raise HTTPException(
                status_code=400, 
                detail=f"ロールID {assignment.role_id} が見つかりません"
            )
        
        # 既存の割り当てを確認
        existing = db.query(UserRole).filter(
            UserRole.user_id == user_id,
            UserRole.role_id == assignment.role_id,
            UserRole.project_id == assignment.project_id
        ).first()
        
        if not existing:
            # 新しいロール割り当てを作成
            user_role = UserRole(
                user_id=user_id,
                role_id=assignment.role_id,
                project_id=assignment.project_id
            )
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
        user_role = db.query(UserRole).filter(
            UserRole.id == user_role_id,
            UserRole.user_id == user_id
        ).first()
        
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
    user_role = db.query(UserRole).filter(
        UserRole.id == request.user_role_id,
        UserRole.user_id == user_id
    ).first()
    
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
    
    return [
        RoleResponse(
            id=role.id,
            name=role.name,
            description=role.description
        )
        for role in roles
    ]