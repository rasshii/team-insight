"""
ユーザー管理 API エンドポイント (Phase 0: 組織コンテキスト対応)

Phase 0 で旧 RBAC ロール割り当てエンドポイントを廃止し、
組織内メンバー管理は /api/v1/organizations/{id}/members に集約した。

このルーターでは以下のみ提供する:
- GET /            : 組織内ユーザー一覧 (Org Admin)
- GET /{user_id}   : ユーザー詳細 (Org Admin or 本人)
- PATCH /{user_id} : ユーザー基本情報更新 (Org Admin or 本人)
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_db_session, get_tenant_context
from app.core.tenant import TenantContext
from app.models.organization_member import OrganizationMember
from app.models.user import User
from app.schemas.auth import OrganizationMembershipResponse
from app.schemas.users import UserListResponse, UserResponse, UserUpdate

router = APIRouter()


def _ensure_org_admin_or_self(tenant: TenantContext, target_user_id: int) -> None:
    """対象ユーザー本人または組織内 ADMIN / System Admin であることを保証"""
    if tenant.is_system_admin:
        return
    if tenant.user.id == target_user_id:
        return
    if not tenant.is_org_admin():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="この操作には組織管理者権限が必要です",
        )


def _to_user_response(user: User) -> UserResponse:
    organizations = [
        OrganizationMembershipResponse(
            organization_id=m.organization_id,
            organization_name=m.organization.name if m.organization else None,
            organization_slug=m.organization.slug if m.organization else None,
            role=m.role,
        )
        for m in (user.organization_memberships or [])
    ]
    return UserResponse(
        id=user.id,
        email=user.email,
        name=user.name,
        is_active=user.is_active,
        is_system_admin=bool(user.is_system_admin),
        organizations=organizations,
        timezone=user.timezone or "Asia/Tokyo",
        locale=user.locale or "ja",
        date_format=user.date_format or "YYYY-MM-DD",
        created_at=user.created_at,
        updated_at=user.updated_at,
    )


@router.get("/", response_model=UserListResponse)
def list_users(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None, description="名前 / メールでの部分一致検索"),
    is_active: Optional[bool] = Query(None),
    tenant: TenantContext = Depends(get_tenant_context),
    db: Session = Depends(get_db_session),
) -> UserListResponse:
    """
    組織内ユーザー一覧を取得 (Org Admin)

    System Admin は active_org_id が指定されていればその組織のユーザー一覧、
    指定されていなければ全ユーザー一覧を取得する。
    """
    if not tenant.is_system_admin and not tenant.is_org_admin():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="この操作には組織管理者権限が必要です",
        )

    query = db.query(User).options(
        joinedload(User.organization_memberships).joinedload(
            OrganizationMember.organization
        )
    )

    # 組織スコープ
    if tenant.active_org_id is not None:
        query = (
            query.join(
                OrganizationMember, OrganizationMember.user_id == User.id
            )
            .filter(OrganizationMember.organization_id == tenant.active_org_id)
            .distinct()
        )
    elif not tenant.is_system_admin:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="組織コンテキストが必要です",
        )

    if search:
        pattern = f"%{search}%"
        query = query.filter(
            or_(
                User.name.ilike(pattern),
                User.full_name.ilike(pattern),
                User.email.ilike(pattern),
            )
        )

    if is_active is not None:
        query = query.filter(User.is_active.is_(is_active))

    total = query.count()
    offset = (page - 1) * per_page
    users = query.order_by(User.created_at.desc()).offset(offset).limit(per_page).all()

    return UserListResponse(
        users=[_to_user_response(u) for u in users],
        total=total,
        page=page,
        per_page=per_page,
    )


@router.get("/{user_id}", response_model=UserResponse)
def get_user(
    user_id: int,
    tenant: TenantContext = Depends(get_tenant_context),
    db: Session = Depends(get_db_session),
) -> UserResponse:
    """ユーザー詳細を取得 (Org Admin or 本人)"""
    _ensure_org_admin_or_self(tenant, user_id)

    user = (
        db.query(User)
        .options(
            joinedload(User.organization_memberships).joinedload(
                OrganizationMember.organization
            )
        )
        .filter(User.id == user_id)
        .first()
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="ユーザーが見つかりません"
        )

    # 組織内 ADMIN の場合、対象ユーザーが同じ組織のメンバーでなければ 404
    if (
        not tenant.is_system_admin
        and tenant.user.id != user_id
        and tenant.active_org_id is not None
    ):
        if not user.is_member_of_organization(tenant.active_org_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="ユーザーが見つかりません",
            )

    return _to_user_response(user)


@router.patch("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int,
    payload: UserUpdate,
    tenant: TenantContext = Depends(get_tenant_context),
    db: Session = Depends(get_db_session),
) -> UserResponse:
    """ユーザー基本情報の更新 (Org Admin or 本人)"""
    _ensure_org_admin_or_self(tenant, user_id)

    user = (
        db.query(User)
        .options(
            joinedload(User.organization_memberships).joinedload(
                OrganizationMember.organization
            )
        )
        .filter(User.id == user_id)
        .first()
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="ユーザーが見つかりません"
        )

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(user, field, value)

    db.commit()
    db.refresh(user)
    return _to_user_response(user)
