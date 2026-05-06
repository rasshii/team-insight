"""
設定管理 API エンドポイント (Phase 0: System Admin 認可へ移行)

Phase 0 で旧 RBAC を廃止したため、システム設定は System Admin (or legacy superuser)
のみがアクセス可能となった。
"""

from typing import Any, Dict

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_superuser, get_db_session
from app.core.deps import get_response_formatter
from app.core.error_handler import AppException, ErrorCode
from app.core.response_builder import ResponseFormatter
from app.models.user import User
from app.schemas.settings import (
    AllSettings,
    SettingCreate,
    SettingResponse,
    SettingsUpdateRequest,
    SettingUpdate,
)
from app.services.settings_service import settings_service

router = APIRouter()


@router.get("/", response_model=AllSettings)
def get_all_settings(
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_active_superuser),
    formatter: ResponseFormatter = Depends(get_response_formatter),
) -> Dict[str, Any]:
    """全設定を取得する (System Admin)"""
    settings = settings_service.get_all_settings(db)
    return formatter.success(data=settings.model_dump())


@router.get("/{group}", response_model=Dict[str, Any])
def get_settings_by_group(
    group: str,
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_active_superuser),
    formatter: ResponseFormatter = Depends(get_response_formatter),
) -> Dict[str, Any]:
    """グループごとの設定を取得する (System Admin)"""
    if group not in ["email", "security", "system"]:
        raise AppException(
            error_code=ErrorCode.VALIDATION_ERROR,
            detail="無効なグループ名です",
            status_code=status.HTTP_400_BAD_REQUEST,
        )
    settings = settings_service.get_settings_by_group(db, group)
    return formatter.success(data={group: settings})


@router.get("/key/{key}", response_model=SettingResponse)
def get_setting(
    key: str,
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_active_superuser),
    formatter: ResponseFormatter = Depends(get_response_formatter),
) -> Dict[str, Any]:
    """特定の設定を取得する (System Admin)"""
    setting = settings_service.get_setting(db, key)
    response_data = setting.__dict__.copy()
    if setting.is_sensitive:
        response_data["value"] = "********"
    return formatter.success(data=response_data)


@router.put("/{key}", response_model=SettingResponse)
def update_setting(
    key: str,
    update_data: SettingUpdate,
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_active_superuser),
    formatter: ResponseFormatter = Depends(get_response_formatter),
) -> Dict[str, Any]:
    """設定を更新する (System Admin)"""
    setting = settings_service.update_setting(db, key, update_data.value)
    response_data = setting.__dict__.copy()
    if setting.is_sensitive:
        response_data["value"] = "********"
    return formatter.success(
        data=response_data, message=f"設定 '{key}' が更新されました"
    )


@router.put("/", response_model=AllSettings)
def update_all_settings(
    settings_data: SettingsUpdateRequest,
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_active_superuser),
    formatter: ResponseFormatter = Depends(get_response_formatter),
) -> Dict[str, Any]:
    """全設定を一括更新する (System Admin)"""
    updated_settings = settings_service.update_all_settings(db, settings_data)
    return formatter.success(
        data=updated_settings.model_dump(), message="設定が更新されました"
    )


@router.post("/", response_model=SettingResponse)
def create_setting(
    setting_data: SettingCreate,
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_active_superuser),
    formatter: ResponseFormatter = Depends(get_response_formatter),
) -> Dict[str, Any]:
    """新しい設定を作成する (System Admin)"""
    setting = settings_service.create_setting(db, setting_data)
    response_data = setting.__dict__.copy()
    if setting.is_sensitive:
        response_data["value"] = "********"
    return formatter.success(
        data=response_data, message=f"設定 '{setting_data.key}' が作成されました"
    )


@router.delete("/{key}")
def delete_setting(
    key: str,
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_active_superuser),
    formatter: ResponseFormatter = Depends(get_response_formatter),
) -> Dict[str, Any]:
    """設定を削除する (System Admin)"""
    settings_service.delete_setting(db, key)
    return formatter.success(data={"key": key}, message=f"設定 '{key}' が削除されました")
