"""
組織エンドポイント (Phase 0)

主要エンドポイント:
- GET /me               : 自分の所属組織一覧
- GET /{id}             : 組織詳細 (System Admin or 組織メンバー)
- PATCH /{id}           : 組織更新 (Org Admin)
- POST /{id}/members    : メンバー追加 (Org Admin)
- GET /{id}/members     : メンバー一覧 (Org Admin)
- PATCH /{id}/members/{user_id} : ロール変更 (Org Admin)
- DELETE /{id}/members/{user_id}: メンバー削除 (Org Admin)
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, Path, Query, Response, status
from sqlalchemy.orm import Session

from app.api.deps import get_db_session, get_tenant_context
from app.core.tenant import TenantContext
from app.models.organization_member import OrganizationRole
from app.schemas.organization import (
    OrganizationMemberCreate,
    OrganizationMemberResponse,
    OrganizationMemberUpdate,
    OrganizationResponse,
    OrganizationUpdate,
)
from app.services.organization_service import organization_service

router = APIRouter()


def _ensure_org_admin(tenant: TenantContext, organization_id: int) -> None:
    """System Admin または対象組織の Org Admin であることを保証"""
    if tenant.is_system_admin:
        return
    role = tenant.user.get_role_in_organization(organization_id)
    if role != OrganizationRole.ADMIN.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="組織管理者権限が必要です",
        )


def _ensure_org_member(tenant: TenantContext, organization_id: int) -> None:
    """System Admin または対象組織のメンバーであることを保証"""
    if tenant.is_system_admin:
        return
    if not tenant.user.is_member_of_organization(organization_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="組織が見つかりません",
        )


@router.get("/me", response_model=List[OrganizationResponse])
def list_my_organizations(
    tenant: TenantContext = Depends(get_tenant_context),
    db: Session = Depends(get_db_session),
) -> List[OrganizationResponse]:
    """自分の所属組織一覧 (組織切替 UI 用)"""
    organizations = organization_service.list_for_user(db, user_id=tenant.user.id)
    return [OrganizationResponse.model_validate(org) for org in organizations]


@router.get("/{organization_id}", response_model=OrganizationResponse)
def get_organization(
    organization_id: int = Path(..., description="組織 ID"),
    tenant: TenantContext = Depends(get_tenant_context),
    db: Session = Depends(get_db_session),
) -> OrganizationResponse:
    """組織詳細"""
    _ensure_org_member(tenant, organization_id)
    organization = organization_service.get(db, organization_id)
    if not organization or organization.deleted_at is not None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="組織が見つかりません"
        )
    return OrganizationResponse.model_validate(organization)


@router.patch("/{organization_id}", response_model=OrganizationResponse)
def update_organization(
    payload: OrganizationUpdate,
    organization_id: int = Path(...),
    tenant: TenantContext = Depends(get_tenant_context),
    db: Session = Depends(get_db_session),
) -> OrganizationResponse:
    """組織情報の更新 (Org Admin)"""
    _ensure_org_admin(tenant, organization_id)

    organization = organization_service.get(db, organization_id)
    if not organization:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="組織が見つかりません"
        )

    updated = organization_service.update(
        db, organization=organization, fields=payload.model_dump(exclude_unset=True)
    )
    return OrganizationResponse.model_validate(updated)


@router.get("/{organization_id}/members", response_model=List[OrganizationMemberResponse])
def list_organization_members(
    organization_id: int = Path(...),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    tenant: TenantContext = Depends(get_tenant_context),
    db: Session = Depends(get_db_session),
) -> List[OrganizationMemberResponse]:
    """組織メンバー一覧 (Org Admin)"""
    _ensure_org_admin(tenant, organization_id)

    members = organization_service.list_members(
        db, organization_id=organization_id, skip=skip, limit=limit
    )
    return [
        OrganizationMemberResponse(
            id=m.id,
            organization_id=m.organization_id,
            user_id=m.user_id,
            user_email=m.user.email if m.user else None,
            user_name=m.user.name if m.user else None,
            role=m.role,
            joined_at=m.joined_at,
        )
        for m in members
    ]


@router.post(
    "/{organization_id}/members",
    response_model=OrganizationMemberResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_organization_member(
    payload: OrganizationMemberCreate,
    organization_id: int = Path(...),
    tenant: TenantContext = Depends(get_tenant_context),
    db: Session = Depends(get_db_session),
) -> OrganizationMemberResponse:
    """組織メンバー追加 (Org Admin)"""
    _ensure_org_admin(tenant, organization_id)

    membership = organization_service.add_member(
        db,
        organization_id=organization_id,
        user_id=payload.user_id,
        role=payload.role,
    )
    return OrganizationMemberResponse(
        id=membership.id,
        organization_id=membership.organization_id,
        user_id=membership.user_id,
        user_email=membership.user.email if membership.user else None,
        user_name=membership.user.name if membership.user else None,
        role=membership.role,
        joined_at=membership.joined_at,
    )


@router.patch(
    "/{organization_id}/members/{user_id}",
    response_model=OrganizationMemberResponse,
)
def update_organization_member(
    payload: OrganizationMemberUpdate,
    organization_id: int = Path(...),
    user_id: int = Path(...),
    tenant: TenantContext = Depends(get_tenant_context),
    db: Session = Depends(get_db_session),
) -> OrganizationMemberResponse:
    """メンバーロール変更 (Org Admin)"""
    _ensure_org_admin(tenant, organization_id)

    membership = organization_service.update_member_role(
        db,
        organization_id=organization_id,
        user_id=user_id,
        new_role=payload.role,
    )
    return OrganizationMemberResponse(
        id=membership.id,
        organization_id=membership.organization_id,
        user_id=membership.user_id,
        user_email=membership.user.email if membership.user else None,
        user_name=membership.user.name if membership.user else None,
        role=membership.role,
        joined_at=membership.joined_at,
    )


@router.delete(
    "/{organization_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT
)
def remove_organization_member(
    organization_id: int = Path(...),
    user_id: int = Path(...),
    tenant: TenantContext = Depends(get_tenant_context),
    db: Session = Depends(get_db_session),
) -> Response:
    """メンバー削除 (Org Admin)"""
    _ensure_org_admin(tenant, organization_id)
    organization_service.remove_member(
        db, organization_id=organization_id, user_id=user_id
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
