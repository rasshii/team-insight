"""
同期サービスパッケージ

このパッケージは、Backlogからデータを同期する機能を提供します。
単一責任原則に基づいて、各サービスが特定の同期機能を担当します。

パッケージ構成:
- base_sync_service: 共通機能を提供する基底クラス
- user_sync_service: ユーザー情報の同期
- project_sync_service: プロジェクト情報の同期
- task_sync_service: タスク（課題）情報の同期

使用例:
    from app.services.sync import (
        user_sync_service,
        project_sync_service,
        task_sync_service
    )

    # ユーザーをインポート
    result = await user_sync_service.import_users_from_backlog(
        user=current_user,
        access_token=token,
        db=db
    )

    # プロジェクトを同期
    result = await project_sync_service.sync_all_projects(
        user=current_user,
        access_token=token,
        db=db
    )

    # ユーザーのタスクを同期
    result = await task_sync_service.sync_user_tasks(
        user=current_user,
        access_token=token,
        db=db
    )

後方互換性:
    既存のコードとの互換性を保つため、統合サービスクラスも提供されます:
    from app.services.sync import sync_service

設計思想:
    - 単一責任原則: 各サービスは特定の同期機能のみを担当
    - DRY原則: 共通機能は基底クラスで実装
    - 依存性注入: データベースセッションなどを外部から注入
    - テスタビリティ: 各サービスを独立してテスト可能
"""

from app.services.sync.base_sync_service import BaseSyncService
from app.services.sync.user_sync_service import user_sync_service
from app.services.sync.project_sync_service import project_sync_service
from app.services.sync.task_sync_service import task_sync_service

# 後方互換性のため、統合サービスクラスを提供
from app.services.sync.integrated_sync_service import sync_service

__all__ = [
    "BaseSyncService",
    "user_sync_service",
    "project_sync_service",
    "task_sync_service",
    "sync_service",  # 後方互換性のため
]
