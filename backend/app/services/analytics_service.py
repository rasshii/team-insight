"""
プロジェクト分析サービス

プロジェクトの健康度、ボトルネック、パフォーマンス指標を
分析するサービスを提供します。
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from app.models.project import Project
from app.models.task import Task, TaskStatus
from app.models.user import User
import logging

logger = logging.getLogger(__name__)


class AnalyticsService:
    """プロジェクト分析サービス"""
    
    def get_project_health(
        self,
        project_id: int,
        db: Session
    ) -> Dict[str, Any]:
        """
        プロジェクトの健康度を取得
        
        Args:
            project_id: プロジェクトID
            db: データベースセッション
            
        Returns:
            健康度スコアと詳細情報
        """
        try:
            # 単一クエリですべての統計情報を取得
            from sqlalchemy import case, and_
            
            # 基本統計を一度に取得
            stats = db.query(
                func.count(Task.id).label('total'),
                func.sum(case((Task.status == TaskStatus.CLOSED, 1), else_=0)).label('completed'),
                func.sum(case((and_(Task.due_date < datetime.now(), 
                                   Task.status != TaskStatus.CLOSED), 1), else_=0)).label('overdue')
            ).filter(Task.project_id == project_id).first()
            
            total_tasks = stats.total or 0
            completed_tasks = stats.completed or 0
            overdue_tasks = stats.overdue or 0
            
            # ステータスID別分布を単一クエリで取得
            status_counts = db.query(
                Task.status_id,
                func.count(Task.id).label('count')
            ).filter(
                Task.project_id == project_id,
                Task.status_id.isnot(None)  # status_idがNULLでないものだけ集計
            ).group_by(Task.status_id).all()
            
            # status_idベースの分布を作成
            status_distribution = {}
            for status_id, count in status_counts:
                status_distribution[str(status_id)] = count
            
            # 健康度スコアを計算（0-100）
            health_score = self._calculate_health_score(
                total_tasks,
                completed_tasks,
                overdue_tasks
            )
            
            return {
                "health_score": health_score,
                "total_tasks": total_tasks,
                "completed_tasks": completed_tasks,
                "completion_rate": (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0,
                "overdue_tasks": overdue_tasks,
                "overdue_rate": (overdue_tasks / total_tasks * 100) if total_tasks > 0 else 0,
                "status_distribution": status_distribution
            }
            
        except Exception as e:
            logger.error(f"Failed to get project health: {str(e)}")
            raise
    
    def get_bottlenecks(
        self,
        project_id: int,
        db: Session
    ) -> List[Dict[str, Any]]:
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
            stalled_tasks = db.query(
                Task.status,
                func.count(Task.id).label('count'),
                func.avg(
                    func.extract('epoch', datetime.now() - Task.updated_at) / 86400
                ).label('avg_days_stalled')
            ).filter(
                Task.project_id == project_id,
                Task.status != TaskStatus.CLOSED,
                Task.updated_at < datetime.now() - timedelta(days=7)
            ).group_by(Task.status).all()
            
            for status, count, avg_days in stalled_tasks:
                if count > 0:
                    bottlenecks.append({
                        "type": "stalled_tasks",
                        "status": status.value,
                        "count": count,
                        "avg_days_stalled": round(avg_days, 1),
                        "severity": "high" if avg_days > 14 else "medium"
                    })
            
            # 2. 特定ユーザーへのタスク集中を検出
            task_concentration = db.query(
                User.name,
                func.count(Task.id).label('task_count')
            ).join(
                Task, Task.assignee_id == User.id
            ).filter(
                Task.project_id == project_id,
                Task.status.in_([TaskStatus.TODO, TaskStatus.IN_PROGRESS])
            ).group_by(User.id, User.name).all()
            
            if task_concentration:
                avg_tasks = sum(count for _, count in task_concentration) / len(task_concentration)
                for name, count in task_concentration:
                    if count > avg_tasks * 1.5:  # 平均の1.5倍以上
                        bottlenecks.append({
                            "type": "task_concentration",
                            "assignee": name,
                            "task_count": count,
                            "avg_task_count": round(avg_tasks, 1),
                            "severity": "high" if count > avg_tasks * 2 else "medium"
                        })
            
            # 3. 期限切れタスクの担当者を検出
            overdue_by_assignee = db.query(
                User.name,
                func.count(Task.id).label('overdue_count')
            ).join(
                Task, Task.assignee_id == User.id
            ).filter(
                Task.project_id == project_id,
                Task.due_date < datetime.now(),
                Task.status != TaskStatus.CLOSED
            ).group_by(User.id, User.name).all()
            
            for name, count in overdue_by_assignee:
                if count > 0:
                    bottlenecks.append({
                        "type": "overdue_tasks",
                        "assignee": name,
                        "overdue_count": count,
                        "severity": "high" if count > 5 else "medium"
                    })
            
            return bottlenecks
            
        except Exception as e:
            logger.error(f"Failed to detect bottlenecks: {str(e)}")
            raise
    
    def get_velocity_trend(
        self,
        project_id: int,
        db: Session,
        period_days: int = 30
    ) -> List[Dict[str, Any]]:
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
            daily_velocity = db.query(
                func.date(Task.completed_date).label('date'),
                func.count(Task.id).label('completed_count')
            ).filter(
                Task.project_id == project_id,
                Task.status == TaskStatus.CLOSED,
                Task.completed_date >= start_date
            ).group_by(func.date(Task.completed_date)).all()
            
            # 結果を整形
            velocity_data = []
            for date, count in daily_velocity:
                velocity_data.append({
                    "date": date.isoformat() if date else None,
                    "completed_count": count
                })
            
            return velocity_data
            
        except Exception as e:
            logger.error(f"Failed to get velocity trend: {str(e)}")
            raise
    
    def get_cycle_time_analysis(
        self,
        project_id: int,
        db: Session
    ) -> Dict[str, Any]:
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
                    avg_time = db.query(
                        func.avg(
                            func.extract('epoch', Task.completed_date - Task.created_at) / 86400
                        )
                    ).filter(
                        Task.project_id == project_id,
                        Task.status == status,
                        Task.completed_date.isnot(None)
                    ).scalar()
                else:
                    # 未完了タスクは更新日からの経過時間
                    avg_time = db.query(
                        func.avg(
                            func.extract('epoch', datetime.now() - Task.updated_at) / 86400
                        )
                    ).filter(
                        Task.project_id == project_id,
                        Task.status == status
                    ).scalar()
                
                cycle_times[status.value] = round(avg_time, 1) if avg_time else 0
            
            return {
                "cycle_times": cycle_times,
                "unit": "days"
            }
            
        except Exception as e:
            logger.error(f"Failed to get cycle time analysis: {str(e)}")
            raise
    
    def _calculate_health_score(
        self,
        total_tasks: int,
        completed_tasks: int,
        overdue_tasks: int
    ) -> int:
        """
        健康度スコアを計算
        
        Args:
            total_tasks: 総タスク数
            completed_tasks: 完了タスク数
            overdue_tasks: 期限切れタスク数
            
        Returns:
            健康度スコア（0-100）
        """
        if total_tasks == 0:
            return 100
        
        # 完了率のスコア（0-50点）
        completion_score = (completed_tasks / total_tasks) * 50
        
        # 期限遵守率のスコア（0-50点）
        overdue_rate = overdue_tasks / total_tasks
        deadline_score = (1 - overdue_rate) * 50
        
        return int(completion_score + deadline_score)


analytics_service = AnalyticsService()