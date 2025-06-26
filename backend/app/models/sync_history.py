"""
同期履歴を記録するモデル
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, JSON, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from app.db.base_class import Base


class SyncType(str, enum.Enum):
    """同期タイプ"""
    USER_TASKS = "user_tasks"
    PROJECT_TASKS = "project_tasks"
    ALL_PROJECTS = "all_projects"
    SINGLE_ISSUE = "single_issue"
    PROJECT_MEMBERS = "project_members"


class SyncStatus(str, enum.Enum):
    """同期ステータス"""
    STARTED = "started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class SyncHistory(Base):
    """
    同期履歴を記録するモデル
    
    各同期操作の履歴を保存し、成功/失敗の追跡と
    パフォーマンス分析を可能にします。
    """
    __tablename__ = "sync_histories"
    __table_args__ = {'schema': 'team_insight'}

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("team_insight.users.id"), nullable=False)
    sync_type = Column(Enum(SyncType), nullable=False)
    status = Column(Enum(SyncStatus), nullable=False, default=SyncStatus.STARTED)
    
    # 同期対象の詳細
    target_id = Column(Integer, nullable=True)  # プロジェクトIDや課題IDなど
    target_name = Column(String(255), nullable=True)  # 対象の名前（表示用）
    
    # 同期結果
    items_created = Column(Integer, default=0)
    items_updated = Column(Integer, default=0)
    items_failed = Column(Integer, default=0)
    total_items = Column(Integer, default=0)
    
    # エラー情報
    error_message = Column(Text, nullable=True)
    error_details = Column(JSON, nullable=True)  # 詳細なエラー情報
    
    # タイムスタンプ
    started_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    duration_seconds = Column(Integer, nullable=True)  # 実行時間（秒）
    
    # メタデータ
    sync_metadata = Column(JSON, nullable=True)  # その他の情報
    
    # リレーション
    user = relationship("User", back_populates="sync_histories")
    
    def __repr__(self):
        return f"<SyncHistory(id={self.id}, user_id={self.user_id}, type={self.sync_type}, status={self.status})>"
    
    def complete(self, items_created: int = 0, items_updated: int = 0, 
                 items_failed: int = 0, total_items: int = 0):
        """
        同期を完了としてマーク
        
        Args:
            items_created: 作成されたアイテム数
            items_updated: 更新されたアイテム数
            items_failed: 失敗したアイテム数
            total_items: 総アイテム数
        """
        self.status = SyncStatus.COMPLETED
        self.completed_at = datetime.utcnow()
        self.items_created = items_created
        self.items_updated = items_updated
        self.items_failed = items_failed
        self.total_items = total_items
        
        if self.started_at:
            self.duration_seconds = int((self.completed_at - self.started_at).total_seconds())
    
    def fail(self, error_message: str, error_details: dict = None):
        """
        同期を失敗としてマーク
        
        Args:
            error_message: エラーメッセージ
            error_details: 詳細なエラー情報
        """
        self.status = SyncStatus.FAILED
        self.completed_at = datetime.utcnow()
        self.error_message = error_message
        self.error_details = error_details
        
        if self.started_at:
            self.duration_seconds = int((self.completed_at - self.started_at).total_seconds())