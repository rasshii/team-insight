"""
同期サービス（後方互換性のためのエイリアス）

このモジュールは、既存のコードとの後方互換性を保つために存在します。
新しい分割されたサービスを内部で使用し、既存のインターフェースを提供します。

推奨: 新規コードでは、分割されたサービスを直接使用してください：
    from app.services.sync import (
        user_sync_service,
        project_sync_service,
        task_sync_service
    )

後方互換性: 既存のコードは変更せずに動作します：
    from app.services.sync_service import sync_service
    result = await sync_service.sync_user_tasks(user, token, db)

設計思想:
    - 単一責任原則に基づいて、各サービスが特定の同期機能のみを担当
    - 既存のコードを壊さないために、統合サービスクラスを提供
    - DRY原則を適用し、共通機能は基底クラスで実装
"""

# 新しい統合サービスをインポート
from app.services.sync.integrated_sync_service import sync_service

# 後方互換性のため、SyncServiceクラスもエクスポート
from app.services.sync.integrated_sync_service import IntegratedSyncService as SyncService

__all__ = ["sync_service", "SyncService"]
