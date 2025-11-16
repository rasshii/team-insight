"""
設定管理APIエンドポイント
"""

from typing import Any, Dict, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db_session, get_current_active_user
from app.core.permissions import require_role, RoleType
from app.models.user import User
from app.schemas.settings import Setting, SettingResponse, SettingCreate, SettingUpdate, AllSettings, SettingsUpdateRequest
from app.services.settings_service import settings_service
from app.core.response_builder import ResponseFormatter
from app.core.deps import get_response_formatter
from app.core.error_handler import AppException, ErrorCode

router = APIRouter()


@router.get("/", response_model=AllSettings)
@require_role([RoleType.ADMIN])
async def get_all_settings(
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_active_user),
    formatter: ResponseFormatter = Depends(get_response_formatter),
) -> Dict[str, Any]:
    """
    全設定を取得する（管理者のみ）
    """
    settings = settings_service.get_all_settings(db)
    return formatter.success(data=settings.model_dump())


@router.get("/{group}", response_model=Dict[str, Any])
@require_role([RoleType.ADMIN])
async def get_settings_by_group(
    group: str,
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_active_user),
    formatter: ResponseFormatter = Depends(get_response_formatter),
) -> Dict[str, Any]:
    """
    グループごとの設定を取得する（管理者のみ）

    Args:
        group: 設定グループ（email, security, sync, system）
    """
    if group not in ["email", "security", "sync", "system"]:
        raise AppException(
            error_code=ErrorCode.VALIDATION_ERROR, detail="無効なグループ名です", status_code=status.HTTP_400_BAD_REQUEST
        )

    settings = settings_service.get_settings_by_group(db, group)
    return formatter.success(data={group: settings})


@router.get("/key/{key}", response_model=SettingResponse)
@require_role([RoleType.ADMIN])
async def get_setting(
    key: str,
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_active_user),
    formatter: ResponseFormatter = Depends(get_response_formatter),
) -> Dict[str, Any]:
    """
    特定の設定を取得する（管理者のみ）

    Args:
        key: 設定キー
    """
    setting = settings_service.get_setting(db, key)

    # 機密情報はマスク
    response_data = setting.__dict__.copy()
    if setting.is_sensitive:
        response_data["value"] = "********"

    return formatter.success(data=response_data)


@router.put("/{key}", response_model=SettingResponse)
@require_role([RoleType.ADMIN])
async def update_setting(
    key: str,
    update_data: SettingUpdate,
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_active_user),
    formatter: ResponseFormatter = Depends(get_response_formatter),
) -> Dict[str, Any]:
    """
    設定を更新する（管理者のみ）

    Args:
        key: 設定キー
        update_data: 更新データ
    """
    setting = settings_service.update_setting(db, key, update_data.value)

    # 機密情報はマスク
    response_data = setting.__dict__.copy()
    if setting.is_sensitive:
        response_data["value"] = "********"

    return formatter.success(data=response_data, message=f"設定 '{key}' が更新されました")


@router.put("/", response_model=AllSettings)
@require_role([RoleType.ADMIN])
async def update_all_settings(
    settings_data: SettingsUpdateRequest,
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_active_user),
    formatter: ResponseFormatter = Depends(get_response_formatter),
) -> Dict[str, Any]:
    """
    全設定を一括更新する（管理者のみ）

    Args:
        settings_data: 更新する設定データ
    """
    updated_settings = settings_service.update_all_settings(db, settings_data)
    return formatter.success(data=updated_settings.model_dump(), message="設定が更新されました")


@router.post("/", response_model=SettingResponse)
@require_role([RoleType.ADMIN])
async def create_setting(
    setting_data: SettingCreate,
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_active_user),
    formatter: ResponseFormatter = Depends(get_response_formatter),
) -> Dict[str, Any]:
    """
    新しい設定を作成する（管理者のみ）

    Args:
        setting_data: 設定作成データ
    """
    setting = settings_service.create_setting(db, setting_data)

    # 機密情報はマスク
    response_data = setting.__dict__.copy()
    if setting.is_sensitive:
        response_data["value"] = "********"

    return formatter.success(data=response_data, message=f"設定 '{setting_data.key}' が作成されました")


@router.delete("/{key}")
@require_role([RoleType.ADMIN])
async def delete_setting(
    key: str,
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_active_user),
    formatter: ResponseFormatter = Depends(get_response_formatter),
) -> Dict[str, Any]:
    """
    設定を削除する（管理者のみ）

    Args:
        key: 設定キー
    """
    settings_service.delete_setting(db, key)
    return formatter.success(data={"key": key}, message=f"設定 '{key}' が削除されました")
