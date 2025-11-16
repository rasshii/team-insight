"""
プロジェクト分析サービス - データ駆動型インサイト生成モジュール

このモジュールは、プロジェクトのパフォーマンスを定量的に分析し、
以下のインサイトを提供します：

主要機能：
1. プロジェクト健康度スコアの算出
2. ボトルネック検出と優先順位付け
3. ベロシティ（作業速度）のトレンド分析
4. サイクルタイム（リードタイム）の測定

分析アプローチ：
- SQLクエリの最適化によるパフォーマンス向上
- 集計関数を活用した効率的なデータ処理
- N+1問題の回避（適切なJOINとサブクエリの使用）
- リアルタイム計算とキャッシュ戦略のバランス

使用例：
    analytics = AnalyticsService()

    # プロジェクト健康度の取得
    health = analytics.get_project_health(project_id=1, db=db)
    print(f"Health Score: {health['health_score']}/100")

    # ボトルネック検出
    bottlenecks = analytics.get_bottlenecks(project_id=1, db=db)
    for bottleneck in bottlenecks:
        print(f"{bottleneck['type']}: {bottleneck['severity']}")

パフォーマンス考慮事項：
- 大量データに対応した効率的なクエリ設計
- インデックスを活用した高速検索
- 必要最小限のデータのみを取得
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from app.models.project import Project
from app.models.task import Task, TaskStatus
from app.models.user import User
from app.repositories import TaskRepository, ProjectRepository, UserRepository
import logging

logger = logging.getLogger(__name__)


class AnalyticsService:
    """
    プロジェクト分析サービスクラス

    プロジェクトのパフォーマンスメトリクスを計算し、
    チームの生産性向上に役立つインサイトを提供します。

    主要メソッド：
    - get_project_health: プロジェクトの健康度スコアを算出
    - get_bottlenecks: ボトルネック（滞留、過負荷、期限切れ）を検出
    - get_velocity_trend: 日別の完了タスク数を分析
    - get_cycle_time_analysis: ステータス別の滞留時間を計算

    分析指標の定義：
    - 健康度スコア: 0-100の範囲で、完了率と期限遵守率から算出
    - ボトルネック: プロジェクト進行の障害となる要因
    - ベロシティ: 一定期間内に完了したタスク数
    - サイクルタイム: タスクが各ステータスに滞留する平均時間
    """

    def get_project_health(self, project_id: int, db: Session) -> Dict[str, Any]:
        """
        プロジェクトの健康度スコアと詳細メトリクスを算出

        プロジェクトの現状を定量的に評価し、0-100のスコアで表現します。
        完了率と期限遵守率を組み合わせることで、総合的な健康度を判定します。

        算出ロジック：
        1. 基本統計の取得（総タスク数、完了数、期限切れ数）
        2. ステータス別分布の集計
        3. 完了率と期限遵守率から健康度スコアを計算

        健康度スコアの計算式：
        - 完了率スコア: (完了タスク数 / 総タスク数) × 50点
        - 期限遵守スコア: (1 - 期限切れ率) × 50点
        - 合計: 完了率スコア + 期限遵守スコア（0-100点）

        スコアの解釈：
        - 80-100点: 健全（緑）
        - 60-79点: 注意（黄）
        - 0-59点: 警告（赤）

        Repository層の活用：
        - TaskRepositoryを使用してデータアクセスを抽象化
        - 統計情報の取得を効率的に実行
        - ビジネスロジックとデータアクセスの分離

        Args:
            project_id (int): 分析対象のプロジェクトID
            db (Session): SQLAlchemyのデータベースセッション

        Returns:
            Dict[str, Any]: 健康度スコアと詳細メトリクス
                {
                    "health_score": 85,              # 健康度スコア（0-100）
                    "total_tasks": 100,              # 総タスク数
                    "completed_tasks": 80,           # 完了タスク数
                    "completion_rate": 80.0,         # 完了率（%）
                    "overdue_tasks": 5,              # 期限切れタスク数
                    "overdue_rate": 5.0,             # 期限切れ率（%）
                    "status_distribution": {         # ステータス別分布
                        "1": 10,  # 未対応
                        "2": 5,   # 処理中
                        "3": 5,   # 処理済み
                        "4": 80   # 完了
                    }
                }

        Example:
            >>> health = analytics.get_project_health(project_id=1, db=db)
            >>> if health["health_score"] < 60:
            ...     print("プロジェクトが危険な状態です！")
            >>> print(f"完了率: {health['completion_rate']:.1f}%")

        Note:
            - タスク数が0の場合、健康度スコアは100点（問題なし）
            - 期限切れタスクは未完了のタスクのみカウント
            - ステータスIDがNullのタスクは分布から除外
        """
        try:
            # Repository層を初期化
            task_repo = TaskRepository(db)

            # SQLAlchemyのcase式を使用した条件付き集計
            from sqlalchemy import case, and_

            # 基本統計を単一クエリで一括取得（パフォーマンス最適化）
            # CASE式により、複数の条件を1回のスキャンで集計
            stats = (
                db.query(
                    func.count(Task.id).label("total"),
                    # 完了タスク数をカウント
                    func.sum(case((Task.status == TaskStatus.CLOSED, 1), else_=0)).label("completed"),
                    # 期限切れかつ未完了のタスクをカウント
                    func.sum(case((and_(Task.due_date < datetime.now(), Task.status != TaskStatus.CLOSED), 1), else_=0)).label(
                        "overdue"
                    ),
                )
                .filter(Task.project_id == project_id)
                .first()
            )

            # 集計結果を取得（Noneの場合は0にフォールバック）
            total_tasks = stats.total or 0
            completed_tasks = stats.completed or 0
            overdue_tasks = stats.overdue or 0

            # ステータスID別のタスク分布を集計
            # GROUP BYで効率的にグループ化
            status_counts = (
                db.query(Task.status_id, func.count(Task.id).label("count"))
                .filter(Task.project_id == project_id, Task.status_id.isnot(None))  # status_idがNULLでないものだけ集計
                .group_by(Task.status_id)
                .all()
            )

            # ステータスIDをキーとした辞書を作成
            # フロントエンドでの描画に便利な形式
            status_distribution = {}
            for status_id, count in status_counts:
                status_distribution[str(status_id)] = count

            # 健康度スコアを計算（0-100）
            health_score = self._calculate_health_score(total_tasks, completed_tasks, overdue_tasks)

            # 詳細メトリクスを含む結果を返す
            return {
                "health_score": health_score,
                "total_tasks": total_tasks,
                "completed_tasks": completed_tasks,
                # 完了率をパーセンテージで計算（0除算を防止）
                "completion_rate": (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0,
                "overdue_tasks": overdue_tasks,
                # 期限切れ率をパーセンテージで計算
                "overdue_rate": (overdue_tasks / total_tasks * 100) if total_tasks > 0 else 0,
                "status_distribution": status_distribution,
            }

        except Exception as e:
            # エラー発生時は詳細をログに記録
            logger.error(f"Failed to get project health: {str(e)}")
            raise

    def get_bottlenecks(self, project_id: int, db: Session) -> List[Dict[str, Any]]:
        """
        プロジェクトのボトルネックを検出

        Args:
            project_id: プロジェクトID
            db: データベースセッション

        Returns:
            ボトルネック情報のリスト
        """
        try:
            bottlenecks = []

            # 1. 長期間滞留しているタスクを検出
            stalled_tasks = (
                db.query(
                    Task.status,
                    func.count(Task.id).label("count"),
                    func.avg(func.extract("epoch", datetime.now() - Task.updated_at) / 86400).label("avg_days_stalled"),
                )
                .filter(
                    Task.project_id == project_id,
                    Task.status != TaskStatus.CLOSED,
                    Task.updated_at < datetime.now() - timedelta(days=7),
                )
                .group_by(Task.status)
                .all()
            )

            for status, count, avg_days in stalled_tasks:
                if count > 0:
                    bottlenecks.append(
                        {
                            "type": "stalled_tasks",
                            "status": status.value,
                            "count": count,
                            "avg_days_stalled": round(avg_days, 1),
                            "severity": "high" if avg_days > 14 else "medium",
                        }
                    )

            # 2. 特定ユーザーへのタスク集中を検出
            task_concentration = (
                db.query(User.name, func.count(Task.id).label("task_count"))
                .join(Task, Task.assignee_id == User.id)
                .filter(Task.project_id == project_id, Task.status.in_([TaskStatus.TODO, TaskStatus.IN_PROGRESS]))
                .group_by(User.id, User.name)
                .all()
            )

            if task_concentration:
                avg_tasks = sum(count for _, count in task_concentration) / len(task_concentration)
                for name, count in task_concentration:
                    if count > avg_tasks * 1.5:  # 平均の1.5倍以上
                        bottlenecks.append(
                            {
                                "type": "task_concentration",
                                "assignee": name,
                                "task_count": count,
                                "avg_task_count": round(avg_tasks, 1),
                                "severity": "high" if count > avg_tasks * 2 else "medium",
                            }
                        )

            # 3. 期限切れタスクの担当者を検出
            overdue_by_assignee = (
                db.query(User.name, func.count(Task.id).label("overdue_count"))
                .join(Task, Task.assignee_id == User.id)
                .filter(Task.project_id == project_id, Task.due_date < datetime.now(), Task.status != TaskStatus.CLOSED)
                .group_by(User.id, User.name)
                .all()
            )

            for name, count in overdue_by_assignee:
                if count > 0:
                    bottlenecks.append(
                        {
                            "type": "overdue_tasks",
                            "assignee": name,
                            "overdue_count": count,
                            "severity": "high" if count > 5 else "medium",
                        }
                    )

            return bottlenecks

        except Exception as e:
            logger.error(f"Failed to detect bottlenecks: {str(e)}")
            raise

    def get_velocity_trend(self, project_id: int, db: Session, period_days: int = 30) -> List[Dict[str, Any]]:
        """
        プロジェクトのベロシティトレンドを取得

        Args:
            project_id: プロジェクトID
            db: データベースセッション
            period_days: 分析期間（日数）

        Returns:
            日別の完了タスク数
        """
        try:
            start_date = datetime.now() - timedelta(days=period_days)

            # 日別の完了タスク数を集計
            daily_velocity = (
                db.query(func.date(Task.completed_date).label("date"), func.count(Task.id).label("completed_count"))
                .filter(Task.project_id == project_id, Task.status == TaskStatus.CLOSED, Task.completed_date >= start_date)
                .group_by(func.date(Task.completed_date))
                .all()
            )

            # 結果を整形
            velocity_data = []
            for date, count in daily_velocity:
                velocity_data.append({"date": date.isoformat() if date else None, "completed_count": count})

            return velocity_data

        except Exception as e:
            logger.error(f"Failed to get velocity trend: {str(e)}")
            raise

    def get_cycle_time_analysis(self, project_id: int, db: Session) -> Dict[str, Any]:
        """
        サイクルタイム分析を取得

        Args:
            project_id: プロジェクトID
            db: データベースセッション

        Returns:
            ステータス別の平均滞留時間
        """
        try:
            # 各ステータスでの平均滞留時間を計算
            # 注: 実際の実装では、タスクの状態遷移履歴が必要
            # ここでは簡易的に現在のステータスでの滞留時間を計算

            cycle_times = {}
            for status in TaskStatus:
                if status == TaskStatus.CLOSED:
                    # 完了タスクは作成から完了までの時間
                    avg_time = (
                        db.query(func.avg(func.extract("epoch", Task.completed_date - Task.created_at) / 86400))
                        .filter(Task.project_id == project_id, Task.status == status, Task.completed_date.isnot(None))
                        .scalar()
                    )
                else:
                    # 未完了タスクは更新日からの経過時間
                    avg_time = (
                        db.query(func.avg(func.extract("epoch", datetime.now() - Task.updated_at) / 86400))
                        .filter(Task.project_id == project_id, Task.status == status)
                        .scalar()
                    )

                cycle_times[status.value] = round(avg_time, 1) if avg_time else 0

            return {"cycle_times": cycle_times, "unit": "days"}

        except Exception as e:
            logger.error(f"Failed to get cycle time analysis: {str(e)}")
            raise

    def _calculate_health_score(self, total_tasks: int, completed_tasks: int, overdue_tasks: int) -> int:
        """
        プロジェクトの健康度スコアを算出（0-100点）

        2つの主要指標を組み合わせて総合的な健康度を評価します：
        1. 完了率: どれだけのタスクが完了しているか
        2. 期限遵守率: どれだけのタスクが期限内に処理されているか

        計算式の詳細：
        - 完了率スコア = (完了タスク数 / 総タスク数) × 50点
          → 完了率が高いほど高得点（最大50点）
        - 期限遵守スコア = (1 - 期限切れ率) × 50点
          → 期限切れが少ないほど高得点（最大50点）
        - 健康度スコア = 完了率スコア + 期限遵守スコア（0-100点）

        スコアの意味：
        - 100点: 完璧（全タスク完了、期限切れなし）
        - 75点: 完了率50%、期限切れ率0% または 完了率100%、期限切れ率50%
        - 50点: 完了率50%、期限切れ率50%
        - 0点: 完了率0%、期限切れ率100%

        エッジケース：
        - タスクが0件の場合は100点を返す（問題なしと判定）

        Args:
            total_tasks (int): プロジェクトの総タスク数
            completed_tasks (int): 完了済みのタスク数
            overdue_tasks (int): 期限切れのタスク数（未完了のみ）

        Returns:
            int: 健康度スコア（0-100の整数）

        Example:
            >>> # 完璧なプロジェクト
            >>> score = analytics._calculate_health_score(100, 100, 0)
            >>> print(score)  # 100

            >>> # 半分完了、期限切れなし
            >>> score = analytics._calculate_health_score(100, 50, 0)
            >>> print(score)  # 75

            >>> # 全完了だが半分が期限切れ
            >>> score = analytics._calculate_health_score(100, 100, 50)
            >>> print(score)  # 75

        Note:
            - このメソッドはプライベート（外部から直接呼び出さない）
            - スコアは整数に丸められる（小数点以下切り捨て）
        """
        # タスクが0件の場合は満点を返す（問題なしと判定）
        if total_tasks == 0:
            return 100

        # 完了率スコアを計算（0-50点）
        # 完了率 = 完了タスク数 / 総タスク数
        completion_score = (completed_tasks / total_tasks) * 50

        # 期限遵守スコアを計算（0-50点）
        # 期限切れ率 = 期限切れタスク数 / 総タスク数
        overdue_rate = overdue_tasks / total_tasks
        # 期限遵守スコア = (1 - 期限切れ率) × 50
        # 期限切れが少ないほど高得点
        deadline_score = (1 - overdue_rate) * 50

        # 2つのスコアを合計して整数に変換
        return int(completion_score + deadline_score)


analytics_service = AnalyticsService()
