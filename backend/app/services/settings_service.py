"""
設定管理サービス
"""

from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
import json

from app.models.settings import SystemSetting
from app.schemas.settings import (
    SettingCreate,
    SettingUpdate,
    AllSettings,
    EmailSettings,
    SecuritySettings,
    SyncSettings,
    SystemSettings,
    SettingsUpdateRequest,
)
from app.core.exceptions import NotFoundException, ConflictException, ValidationException

import logging

logger = logging.getLogger(__name__)


class SettingsService:
    """設定管理サービス"""

    def get_all_settings(self, db: Session) -> AllSettings:
        """
        全設定を取得

        Args:
            db: データベースセッション

        Returns:
            全設定情報
        """
        settings = db.query(SystemSetting).all()

        # グループごとに設定を整理
        grouped_settings = {"email": {}, "security": {}, "sync": {}, "system": {}}

        for setting in settings:
            value = self._convert_value(setting.value, setting.value_type)
            grouped_settings[setting.group][setting.key] = value

        return AllSettings(
            email=EmailSettings(**grouped_settings["email"]),
            security=SecuritySettings(**grouped_settings["security"]),
            sync=SyncSettings(**grouped_settings["sync"]),
            system=SystemSettings(**grouped_settings["system"]),
        )

    def get_settings_by_group(self, db: Session, group: str) -> Dict[str, Any]:
        """
        グループごとの設定を取得

        Args:
            db: データベースセッション
            group: 設定グループ（email, security, sync, system）

        Returns:
            設定の辞書
        """
        settings = db.query(SystemSetting).filter(SystemSetting.group == group).all()

        result = {}
        for setting in settings:
            value = self._convert_value(setting.value, setting.value_type)
            # 機密情報はマスク
            if setting.is_sensitive:
                value = "********"
            result[setting.key] = value

        return result

    def get_setting(self, db: Session, key: str) -> SystemSetting:
        """
        特定の設定を取得

        Args:
            db: データベースセッション
            key: 設定キー

        Returns:
            設定情報

        Raises:
            NotFoundException: 設定が見つからない場合
        """
        setting = db.query(SystemSetting).filter(SystemSetting.key == key).first()

        if not setting:
            raise NotFoundException(f"設定 '{key}' が見つかりません")

        return setting

    def update_setting(self, db: Session, key: str, value: str) -> SystemSetting:
        """
        設定を更新

        Args:
            db: データベースセッション
            key: 設定キー
            value: 新しい値

        Returns:
            更新された設定

        Raises:
            NotFoundException: 設定が見つからない場合
            ValidationException: 値の検証エラー
        """
        setting = self.get_setting(db, key)

        # 値の型チェック
        if setting.value_type == "integer":
            try:
                int(value)
            except ValueError:
                raise ValidationException(f"'{key}' は整数値である必要があります")
        elif setting.value_type == "boolean":
            if value.lower() not in ["true", "false"]:
                raise ValidationException(f"'{key}' はtrue/falseである必要があります")
        elif setting.value_type == "json":
            try:
                json.loads(value)
            except json.JSONDecodeError:
                raise ValidationException(f"'{key}' は有効なJSON形式である必要があります")

        setting.value = value
        db.commit()
        db.refresh(setting)

        logger.info(f"Setting updated: {key}")

        return setting

    def update_all_settings(self, db: Session, settings_data: SettingsUpdateRequest) -> AllSettings:
        """
        全設定を一括更新

        Args:
            db: データベースセッション
            settings_data: 更新する設定データ

        Returns:
            更新後の全設定
        """
        if settings_data.email:
            for key, value in settings_data.email.model_dump().items():
                self.update_setting(db, key, str(value))

        if settings_data.security:
            for key, value in settings_data.security.model_dump().items():
                self.update_setting(db, key, str(value))

        if settings_data.sync:
            for key, value in settings_data.sync.model_dump().items():
                self.update_setting(db, key, str(value))

        if settings_data.system:
            for key, value in settings_data.system.model_dump().items():
                self.update_setting(db, key, str(value))

        return self.get_all_settings(db)

    def create_setting(self, db: Session, setting_data: SettingCreate) -> SystemSetting:
        """
        新しい設定を作成

        Args:
            db: データベースセッション
            setting_data: 設定作成データ

        Returns:
            作成された設定

        Raises:
            ConflictException: 同じキーの設定が既に存在する場合
        """
        # 既存の設定を確認
        existing = db.query(SystemSetting).filter(SystemSetting.key == setting_data.key).first()

        if existing:
            raise ConflictException(f"設定 '{setting_data.key}' は既に存在します")

        setting = SystemSetting(**setting_data.model_dump())
        db.add(setting)
        db.commit()
        db.refresh(setting)

        logger.info(f"Setting created: {setting_data.key}")

        return setting

    def delete_setting(self, db: Session, key: str) -> None:
        """
        設定を削除

        Args:
            db: データベースセッション
            key: 設定キー

        Raises:
            NotFoundException: 設定が見つからない場合
        """
        setting = self.get_setting(db, key)

        db.delete(setting)
        db.commit()

        logger.info(f"Setting deleted: {key}")

    def _convert_value(self, value: str, value_type: str) -> Any:
        """
        文字列値を適切な型に変換

        Args:
            value: 文字列値
            value_type: 値の型

        Returns:
            変換された値
        """
        if value_type == "integer":
            return int(value)
        elif value_type == "boolean":
            return value.lower() == "true"
        elif value_type == "json":
            return json.loads(value)
        else:
            return value


# シングルトンインスタンス
settings_service = SettingsService()
