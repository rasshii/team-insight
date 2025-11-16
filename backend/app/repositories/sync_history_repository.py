"""
同期履歴リポジトリ - 同期履歴データアクセス層

このモジュールは、同期履歴モデルに特化したデータアクセスメソッドを提供します。

主要機能：
1. 同期履歴の基本的なCRUD操作
2. ユーザー、同期タイプ、ステータスによる検索
3. 同期履歴の統計情報取得
4. 最近の同期履歴の取得
5. 失敗した同期の検出

パフォーマンス最適化：
- インデックスを活用した高速検索
- 集計クエリの最適化
- 効率的なフィルタリング

使用例：
    sync_repo = SyncHistoryRepository(db)

    # ユーザーの同期履歴を取得
    histories = sync_repo.get_user_histories(user_id=1, limit=10)

    # 失敗した同期を取得
    failed = sync_repo.get_failed_syncs(user_id=1)

    # 同期統計を取得
    stats = sync_repo.get_sync_statistics(user_id=1)
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, and_, desc

from app.models.sync_history import SyncHistory, SyncType, SyncStatus
from app.repositories.base_repository import BaseRepository


class SyncHistoryRepository(BaseRepository[SyncHistory]):
    """
    同期履歴リポジトリクラス

    同期履歴モデルに対する専用のデータアクセスメソッドを提供します。
    BaseRepositoryの汎用メソッドに加え、同期履歴の特有機能を実装。

    主要メソッド：
    - get_user_histories: ユーザーの同期履歴を取得
    - get_recent_histories: 最近の同期履歴を取得
    - get_failed_syncs: 失敗した同期を取得
    - get_sync_statistics: 同期統計情報を取得
    - get_last_sync: 最後の同期を取得

    パフォーマンス分析：
    - 同期の成功率を算出
    - 平均同期時間を計算
    - 失敗パターンの分析
    """

    def __init__(self, db: Session):
        """
        SyncHistoryRepositoryの初期化

        Args:
            db (Session): SQLAlchemyのデータベースセッション
        """
        super().__init__(SyncHistory, db)

    def get_user_histories(
        self,
        user_id: int,
        sync_type: Optional[SyncType] = None,
        status: Optional[SyncStatus] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[SyncHistory]:
        """
        ユーザーの同期履歴を取得

        特定のユーザーの同期履歴を取得します。
        同期タイプやステータスでフィルタリング可能。

        Args:
            user_id (int): ユーザーID
            sync_type (Optional[SyncType], optional):
                同期タイプで絞り込み。Noneの場合は全タイプ
            status (Optional[SyncStatus], optional):
                ステータスで絞り込み。Noneの場合は全ステータス
            skip (int, optional): スキップするレコード数。デフォルトは0
            limit (int, optional): 取得する最大レコード数。デフォルトは100

        Returns:
            List[SyncHistory]: 同期履歴のリスト

        Example:
            >>> # 全同期履歴を取得
            >>> histories = sync_repo.get_user_histories(user_id=1, limit=20)

            >>> # 失敗した同期のみ取得
            >>> failed = sync_repo.get_user_histories(
            ...     user_id=1, status=SyncStatus.FAILED
            ... )

            >>> # プロジェクトタスク同期のみ取得
            >>> project_syncs = sync_repo.get_user_histories(
            ...     user_id=1, sync_type=SyncType.PROJECT_TASKS
            ... )

        Note:
            - 開始日時の降順でソート（最新のものが先）
            - ユーザー情報も効率的に取得（joinedload）
        """
        query = self.db.query(SyncHistory).options(joinedload(SyncHistory.user)).filter(SyncHistory.user_id == user_id)

        # フィルタ条件の適用
        if sync_type is not None:
            query = query.filter(SyncHistory.sync_type == sync_type)

        if status is not None:
            query = query.filter(SyncHistory.status == status)

        # 開始日時の降順でソート
        query = query.order_by(desc(SyncHistory.started_at))

        return query.offset(skip).limit(limit).all()

    def get_recent_histories(
        self, days: int = 7, sync_type: Optional[SyncType] = None, skip: int = 0, limit: int = 100
    ) -> List[SyncHistory]:
        """
        最近の同期履歴を取得

        指定された期間内の同期履歴を取得します。
        全ユーザーの履歴を対象とし、管理者用の機能として使用します。

        Args:
            days (int, optional): 過去何日間の履歴を取得するか。デフォルトは7日
            sync_type (Optional[SyncType], optional):
                同期タイプで絞り込み。Noneの場合は全タイプ
            skip (int, optional): スキップするレコード数。デフォルトは0
            limit (int, optional): 取得する最大レコード数。デフォルトは100

        Returns:
            List[SyncHistory]: 同期履歴のリスト

        Example:
            >>> # 過去7日間の同期履歴
            >>> recent = sync_repo.get_recent_histories(days=7)

            >>> # 過去30日間のプロジェクトタスク同期
            >>> recent = sync_repo.get_recent_histories(
            ...     days=30, sync_type=SyncType.PROJECT_TASKS
            ... )

        Note:
            - ユーザー情報も効率的に取得
            - 開始日時の降順でソート
        """
        start_date = datetime.utcnow() - timedelta(days=days)

        query = self.db.query(SyncHistory).options(joinedload(SyncHistory.user)).filter(SyncHistory.started_at >= start_date)

        # フィルタ条件の適用
        if sync_type is not None:
            query = query.filter(SyncHistory.sync_type == sync_type)

        # 開始日時の降順でソート
        query = query.order_by(desc(SyncHistory.started_at))

        return query.offset(skip).limit(limit).all()

    def get_failed_syncs(
        self,
        user_id: Optional[int] = None,
        sync_type: Optional[SyncType] = None,
        days: Optional[int] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[SyncHistory]:
        """
        失敗した同期を取得

        ステータスがFAILEDの同期履歴を取得します。
        エラー分析やトラブルシューティングに使用します。

        Args:
            user_id (Optional[int], optional):
                ユーザーIDで絞り込み。Noneの場合は全ユーザー
            sync_type (Optional[SyncType], optional):
                同期タイプで絞り込み。Noneの場合は全タイプ
            days (Optional[int], optional):
                過去何日間の履歴を取得するか。Noneの場合は制限なし
            skip (int, optional): スキップするレコード数。デフォルトは0
            limit (int, optional): 取得する最大レコード数。デフォルトは100

        Returns:
            List[SyncHistory]: 失敗した同期のリスト

        Example:
            >>> # 全ユーザーの失敗した同期
            >>> failed = sync_repo.get_failed_syncs()

            >>> # 特定ユーザーの失敗した同期
            >>> failed = sync_repo.get_failed_syncs(user_id=1)

            >>> # 過去7日間の失敗した同期
            >>> failed = sync_repo.get_failed_syncs(days=7)

        Note:
            - エラーメッセージやエラー詳細も含まれる
            - 開始日時の降順でソート
        """
        query = (
            self.db.query(SyncHistory).options(joinedload(SyncHistory.user)).filter(SyncHistory.status == SyncStatus.FAILED)
        )

        # フィルタ条件の適用
        if user_id is not None:
            query = query.filter(SyncHistory.user_id == user_id)

        if sync_type is not None:
            query = query.filter(SyncHistory.sync_type == sync_type)

        if days is not None:
            start_date = datetime.utcnow() - timedelta(days=days)
            query = query.filter(SyncHistory.started_at >= start_date)

        # 開始日時の降順でソート
        query = query.order_by(desc(SyncHistory.started_at))

        return query.offset(skip).limit(limit).all()

    def get_last_sync(self, user_id: int, sync_type: Optional[SyncType] = None) -> Optional[SyncHistory]:
        """
        最後の同期を取得

        ユーザーの最新の同期履歴を取得します。
        次回の同期タイミングを判断するために使用します。

        Args:
            user_id (int): ユーザーID
            sync_type (Optional[SyncType], optional):
                同期タイプで絞り込み。Noneの場合は全タイプの中から最新を取得

        Returns:
            Optional[SyncHistory]:
                見つかった場合は最新の同期履歴、見つからない場合はNone

        Example:
            >>> # 最後の同期（全タイプ）
            >>> last = sync_repo.get_last_sync(user_id=1)
            >>> if last:
            ...     print(f"Last sync: {last.started_at}")

            >>> # 最後のプロジェクトタスク同期
            >>> last = sync_repo.get_last_sync(
            ...     user_id=1, sync_type=SyncType.PROJECT_TASKS
            ... )

        Note:
            - 開始日時でソートして最新のものを取得
        """
        query = self.db.query(SyncHistory).filter(SyncHistory.user_id == user_id)

        # フィルタ条件の適用
        if sync_type is not None:
            query = query.filter(SyncHistory.sync_type == sync_type)

        # 開始日時の降順でソートして最初の1件を取得
        return query.order_by(desc(SyncHistory.started_at)).first()

    def get_sync_statistics(
        self, user_id: Optional[int] = None, sync_type: Optional[SyncType] = None, days: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        同期統計情報を取得

        同期の成功率、平均時間、総件数などの統計情報を集計します。

        集計される統計情報：
        - total_syncs: 総同期回数
        - successful_syncs: 成功した同期回数
        - failed_syncs: 失敗した同期回数
        - success_rate: 成功率（%）
        - avg_duration: 平均同期時間（秒）
        - total_items_synced: 同期された総アイテム数

        Args:
            user_id (Optional[int], optional):
                ユーザーIDで絞り込み。Noneの場合は全ユーザー
            sync_type (Optional[SyncType], optional):
                同期タイプで絞り込み。Noneの場合は全タイプ
            days (Optional[int], optional):
                過去何日間の統計を取得するか。Noneの場合は全期間

        Returns:
            Dict[str, Any]: 同期統計情報の辞書

        Example:
            >>> # ユーザーの全期間統計
            >>> stats = sync_repo.get_sync_statistics(user_id=1)
            >>> print(f"Success rate: {stats['success_rate']:.1f}%")

            >>> # 過去30日間の統計
            >>> stats = sync_repo.get_sync_statistics(user_id=1, days=30)

        Note:
            - 1回のクエリで複数の統計を効率的に取得
            - CASE式による条件付き集計を活用
        """
        from sqlalchemy import case

        # ベースクエリ
        query = self.db.query(SyncHistory)

        # フィルタ条件の適用
        if user_id is not None:
            query = query.filter(SyncHistory.user_id == user_id)

        if sync_type is not None:
            query = query.filter(SyncHistory.sync_type == sync_type)

        if days is not None:
            start_date = datetime.utcnow() - timedelta(days=days)
            query = query.filter(SyncHistory.started_at >= start_date)

        # 統計情報を一括取得
        stats = query.with_entities(
            func.count(SyncHistory.id).label("total"),
            func.sum(case((SyncHistory.status == SyncStatus.COMPLETED, 1), else_=0)).label("successful"),
            func.sum(case((SyncHistory.status == SyncStatus.FAILED, 1), else_=0)).label("failed"),
            func.avg(SyncHistory.duration_seconds).label("avg_duration"),
            func.sum(SyncHistory.items_created + SyncHistory.items_updated).label("total_items"),
        ).first()

        total_syncs = stats.total or 0
        successful_syncs = stats.successful or 0
        failed_syncs = stats.failed or 0
        avg_duration = stats.avg_duration or 0
        total_items = stats.total_items or 0

        # 成功率を計算
        success_rate = (successful_syncs / total_syncs * 100) if total_syncs > 0 else 0

        return {
            "total_syncs": total_syncs,
            "successful_syncs": successful_syncs,
            "failed_syncs": failed_syncs,
            "success_rate": round(success_rate, 1),
            "avg_duration_seconds": round(avg_duration, 1),
            "total_items_synced": total_items or 0,
        }

    def get_sync_trends(self, user_id: Optional[int] = None, days: int = 30) -> List[Dict[str, Any]]:
        """
        同期のトレンドデータを取得

        日別の同期回数と成功率を集計します。
        ダッシュボードでのグラフ表示に使用します。

        Args:
            user_id (Optional[int], optional):
                ユーザーIDで絞り込み。Noneの場合は全ユーザー
            days (int, optional): 過去何日間のトレンドを取得するか。デフォルトは30日

        Returns:
            List[Dict[str, Any]]: 日別のトレンドデータ

        Example:
            >>> # 過去30日間のトレンド
            >>> trends = sync_repo.get_sync_trends(user_id=1, days=30)
            >>> for trend in trends:
            ...     print(f"{trend['date']}: {trend['total_syncs']} syncs")

        Note:
            - date_truncを使用して日別に集計
            - 成功率も同時に計算
        """
        from sqlalchemy import case

        start_date = datetime.utcnow() - timedelta(days=days)

        # ベースクエリ
        query = self.db.query(SyncHistory).filter(SyncHistory.started_at >= start_date)

        # フィルタ条件の適用
        if user_id is not None:
            query = query.filter(SyncHistory.user_id == user_id)

        # 日別に集計
        trends = (
            query.with_entities(
                func.date(SyncHistory.started_at).label("date"),
                func.count(SyncHistory.id).label("total"),
                func.sum(case((SyncHistory.status == SyncStatus.COMPLETED, 1), else_=0)).label("successful"),
                func.sum(case((SyncHistory.status == SyncStatus.FAILED, 1), else_=0)).label("failed"),
            )
            .group_by(func.date(SyncHistory.started_at))
            .all()
        )

        # 結果を整形
        trend_data = []
        for date, total, successful, failed in trends:
            success_rate = (successful / total * 100) if total > 0 else 0
            trend_data.append(
                {
                    "date": date.isoformat() if date else None,
                    "total_syncs": total or 0,
                    "successful_syncs": successful or 0,
                    "failed_syncs": failed or 0,
                    "success_rate": round(success_rate, 1),
                }
            )

        return trend_data

    def count_user_syncs(self, user_id: int, status: Optional[SyncStatus] = None) -> int:
        """
        ユーザーの同期回数をカウント

        Args:
            user_id (int): ユーザーID
            status (Optional[SyncStatus], optional):
                ステータスで絞り込み。Noneの場合は全ステータス

        Returns:
            int: 同期回数

        Example:
            >>> # 全同期回数
            >>> total = sync_repo.count_user_syncs(user_id=1)

            >>> # 成功した同期回数
            >>> successful = sync_repo.count_user_syncs(
            ...     user_id=1, status=SyncStatus.COMPLETED
            ... )

        Note:
            - COUNT(*)による高速カウント
        """
        query = self.db.query(func.count(SyncHistory.id)).filter(SyncHistory.user_id == user_id)

        if status is not None:
            query = query.filter(SyncHistory.status == status)

        return query.scalar() or 0
