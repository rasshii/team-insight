"""
System Admin 専用 組織管理エンドポイント (Phase 0)

組織の作成・全件参照・soft delete は System Admin のみ実行可能。
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, Path, Query, Response, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user, get_db_session
from app.models.user import User
from app.schemas.organization import (
    OrganizationCreate,
    OrganizationResponse,
)
from app.services.organization_service import organization_service

router = APIRouter()


def _ensure_system_admin(user: User) -> None:
    if not user.is_system_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="System Admin 権限が必要です",
        )


@router.get("", response_model=List[OrganizationResponse])
def list_all_organizations(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db_session),
) -> List[OrganizationResponse]:
    """全組織一覧 (System Admin)"""
    _ensure_system_admin(current_user)
    organizations = organization_service.list_all(db, skip=skip, limit=limit)
    return [OrganizationResponse.model_validate(org) for org in organizations]


@router.post("", response_model=OrganizationResponse, status_code=status.HTTP_201_CREATED)
def create_organization(
    payload: OrganizationCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db_session),
) -> OrganizationResponse:
    """組織作成 (System Admin)"""
    _ensure_system_admin(current_user)
    organization = organization_service.create(
        db,
        name=payload.name,
        slug=payload.slug,
        fiscal_year_start_month=payload.fiscal_year_start_month,
        timezone_str=payload.timezone,
        settings_value=payload.settings,
    )
    return OrganizationResponse.model_validate(organization)


@router.delete("/{organization_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_organization(
    organization_id: int = Path(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db_session),
) -> Response:
    """組織を soft delete (System Admin)"""
    _ensure_system_admin(current_user)
    organization = organization_service.get(db, organization_id)
    if not organization:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="組織が見つかりません"
        )
    organization_service.soft_delete(db, organization=organization)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
