"""
リポジトリ層 - データアクセス層の集約モジュール

このモジュールは、すべてのリポジトリクラスをインポートし、
外部から簡単にアクセスできるようにします。

リポジトリ層の役割：
1. データアクセスロジックの抽象化
2. SQLクエリの一元管理
3. N+1問題の回避
4. ビジネスロジックとデータアクセスの分離

使用例：
    from app.repositories import UserRepository, TaskRepository

    # リポジトリの初期化
    user_repo = UserRepository(db)
    task_repo = TaskRepository(db)

    # データの取得
    user = user_repo.get_by_email("user@example.com")
    tasks = task_repo.get_user_tasks(user_id=user.id)

設計原則：
- 単一責任の原則（データアクセスのみ）
- 依存性注入（Sessionを外部から受け取る）
- インターフェースの一貫性
- パフォーマンスの最適化

利点：
- テスタビリティの向上（モックの容易さ）
- コードの重複排除
- SQLクエリの最適化
- Service層のビジネスロジックへの集中
"""

from app.repositories.base_repository import BaseRepository
from app.repositories.user_repository import UserRepository
from app.repositories.project_repository import ProjectRepository
from app.repositories.task_repository import TaskRepository
from app.repositories.team_repository import TeamRepository
from app.repositories.oauth_token_repository import OAuthTokenRepository
from app.repositories.sync_history_repository import SyncHistoryRepository

__all__ = [
    # 基底クラス
    "BaseRepository",
    # 各リポジトリクラス
    "UserRepository",
    "ProjectRepository",
    "TaskRepository",
    "TeamRepository",
    "OAuthTokenRepository",
    "SyncHistoryRepository",
]
