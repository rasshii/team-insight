"""
分析レポート生成サービス

このモジュールは、分析データから定期配信用のレポートを生成します。
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, case, and_

from app.models.user import User
from app.models.task import Task, TaskStatus
from app.models.project import Project, project_members
from app.services.analytics_service import analytics_service
from app.core.config import settings

logger = logging.getLogger(__name__)


class ReportGenerator:
    """レポート生成サービスクラス"""
    
    def generate_personal_report(
        self,
        user: User,
        db: Session,
        report_type: str = "weekly"
    ) -> Dict[str, Any]:
        """
        個人レポートを生成
        
        Args:
            user: 対象ユーザー
            db: データベースセッション
            report_type: レポートタイプ（daily, weekly, monthly）
            
        Returns:
            レポートデータ
        """
        period_days = self._get_period_days(report_type)
        start_date = datetime.now() - timedelta(days=period_days)
        end_date = datetime.now()
        
        # 基本統計を取得
        stats = db.query(
            func.count(Task.id).label('total'),
            func.sum(case((Task.status == TaskStatus.CLOSED, 1), else_=0)).label('completed'),
            func.sum(case((Task.status == TaskStatus.IN_PROGRESS, 1), else_=0)).label('in_progress'),
            func.sum(case((and_(Task.due_date < datetime.now(), 
                               Task.status != TaskStatus.CLOSED), 1), else_=0)).label('overdue')
        ).filter(
            Task.assignee_id == user.id,
            Task.created_at >= start_date
        ).first()
        
        # 平均サイクルタイム
        avg_cycle_time = db.query(
            func.avg(
                func.extract('epoch', Task.completed_date - Task.created_at) / 86400
            )
        ).filter(
            Task.assignee_id == user.id,
            Task.status == TaskStatus.CLOSED,
            Task.completed_date >= start_date,
            Task.completed_date.isnot(None)
        ).scalar()
        
        # 生産性スコア（簡易計算：完了率 * 期限遵守率）
        completion_rate = (stats.completed / stats.total * 100) if stats.total > 0 else 0
        
        # 期限遵守率
        deadline_stats = db.query(
            func.count(Task.id).label('total_with_deadline'),
            func.sum(
                case(
                    (and_(Task.status == TaskStatus.CLOSED, 
                          Task.completed_date <= Task.due_date), 1),
                    else_=0
                )
            ).label('completed_on_time')
        ).filter(
            Task.assignee_id == user.id,
            Task.due_date.isnot(None),
            Task.created_at >= start_date
        ).first()
        
        deadline_adherence_rate = 0
        if deadline_stats.total_with_deadline > 0:
            deadline_adherence_rate = (
                deadline_stats.completed_on_time / 
                deadline_stats.total_with_deadline * 100
            )
        
        productivity_score = int((completion_rate + deadline_adherence_rate) / 2)
        
        # タスクタイプ別サマリー
        task_type_summary = db.query(
            Task.issue_type_name,
            func.count(Task.id).label('count')
        ).filter(
            Task.assignee_id == user.id,
            Task.status == TaskStatus.CLOSED,
            Task.completed_date >= start_date
        ).group_by(Task.issue_type_name).all()
        
        # レポートデータを構築
        report_data = {
            "user_name": user.name,
            "user_email": user.email,
            "report_type_label": self._get_report_type_label(report_type),
            "report_period": self._get_period_string(report_type, start_date, end_date),
            "completed_tasks": stats.completed or 0,
            "in_progress_tasks": stats.in_progress or 0,
            "overdue_tasks": stats.overdue or 0,
            "avg_cycle_time": round(avg_cycle_time, 1) if avg_cycle_time else 0,
            "productivity_score": productivity_score,
            "completion_rate": round(completion_rate, 1),
            "deadline_adherence_rate": round(deadline_adherence_rate, 1),
            "task_types": [
                {"type": task_type or "未分類", "count": count}
                for task_type, count in task_type_summary
                if count > 0
            ],
            "dashboard_url": f"{settings.FRONTEND_URL}/dashboard/personal",
            "generated_at": datetime.now()
        }
        
        return report_data
    
    def generate_project_report(
        self,
        project: Project,
        db: Session,
        report_type: str = "weekly"
    ) -> Dict[str, Any]:
        """
        プロジェクトレポートを生成
        
        Args:
            project: 対象プロジェクト
            db: データベースセッション
            report_type: レポートタイプ（daily, weekly, monthly）
            
        Returns:
            レポートデータ
        """
        period_days = self._get_period_days(report_type)
        start_date = datetime.now() - timedelta(days=period_days)
        end_date = datetime.now()
        
        # プロジェクト健康度を取得
        health_data = analytics_service.get_project_health(project.id, db)
        
        # ボトルネック情報を取得
        bottlenecks = analytics_service.get_bottlenecks(project.id, db)
        
        # 期間中のタスク統計
        stats = db.query(
            func.count(Task.id).label('total'),
            func.sum(case((Task.status == TaskStatus.CLOSED, 1), else_=0)).label('completed'),
            func.sum(case((Task.status == TaskStatus.IN_PROGRESS, 1), else_=0)).label('in_progress')
        ).filter(
            Task.project_id == project.id,
            Task.created_at >= start_date
        ).first()
        
        # トップパフォーマー（期間中の完了タスク数上位）
        top_performers_data = db.query(
            User.name,
            func.count(Task.id).label('completed_tasks'),
            func.avg(
                func.extract('epoch', Task.completed_date - Task.created_at) / 86400
            ).label('avg_completion_time')
        ).join(
            Task, Task.assignee_id == User.id
        ).filter(
            Task.project_id == project.id,
            Task.status == TaskStatus.CLOSED,
            Task.completed_date >= start_date
        ).group_by(User.id, User.name).order_by(
            func.count(Task.id).desc()
        ).limit(5).all()
        
        top_performers = [
            {
                "name": name,
                "completed_tasks": completed,
                "avg_completion_time": round(avg_time, 1) if avg_time else 0
            }
            for name, completed, avg_time in top_performers_data
        ]
        
        # レポートデータを構築
        report_data = {
            "project_name": project.name,
            "report_type_label": self._get_report_type_label(report_type),
            "report_period": self._get_period_string(report_type, start_date, end_date),
            "health_score": health_data.get("health_score", 0),
            "completed_tasks": stats.completed or 0,
            "in_progress_tasks": stats.in_progress or 0,
            "total_tasks": stats.total or 0,
            "avg_cycle_time": health_data.get("avg_cycle_time", 0),
            "productivity_score": health_data.get("productivity_score", 0),
            "bottleneck_count": len(bottlenecks),
            "critical_bottlenecks": [b for b in bottlenecks if b.get("severity") == "high"][:3],
            "top_performers": top_performers,
            "dashboard_url": f"{settings.FRONTEND_URL}/dashboard/project/{project.id}",
            "generated_at": datetime.now()
        }
        
        return report_data
    
    def generate_team_report(
        self,
        db: Session,
        report_type: str = "weekly"
    ) -> Dict[str, Any]:
        """
        チーム全体のレポートを生成
        
        Args:
            db: データベースセッション
            report_type: レポートタイプ（daily, weekly, monthly）
            
        Returns:
            レポートデータ
        """
        period_days = self._get_period_days(report_type)
        start_date = datetime.now() - timedelta(days=period_days)
        end_date = datetime.now()
        
        # 全体統計
        overall_stats = db.query(
            func.count(Task.id).label('total'),
            func.sum(case((Task.status == TaskStatus.CLOSED, 1), else_=0)).label('completed'),
            func.count(func.distinct(Task.project_id)).label('active_projects'),
            func.count(func.distinct(Task.assignee_id)).label('active_members')
        ).filter(
            Task.created_at >= start_date
        ).first()
        
        # プロジェクト別サマリー
        project_summary = db.query(
            Project.name,
            func.count(Task.id).label('task_count'),
            func.sum(case((Task.status == TaskStatus.CLOSED, 1), else_=0)).label('completed_count')
        ).join(
            Task, Task.project_id == Project.id
        ).filter(
            Task.created_at >= start_date
        ).group_by(Project.id, Project.name).all()
        
        project_data = [
            {
                "name": name,
                "total_tasks": count,
                "completed_tasks": completed,
                "completion_rate": round((completed / count * 100) if count > 0 else 0, 1)
            }
            for name, count, completed in project_summary
        ]
        
        # レポートデータを構築
        report_data = {
            "report_type_label": self._get_report_type_label(report_type),
            "report_period": self._get_period_string(report_type, start_date, end_date),
            "total_tasks": overall_stats.total or 0,
            "completed_tasks": overall_stats.completed or 0,
            "active_projects": overall_stats.active_projects or 0,
            "active_members": overall_stats.active_members or 0,
            "overall_completion_rate": round(
                (overall_stats.completed / overall_stats.total * 100) 
                if overall_stats.total > 0 else 0, 1
            ),
            "project_summary": project_data,
            "dashboard_url": f"{settings.FRONTEND_URL}/dashboard/organization",
            "generated_at": datetime.now()
        }
        
        return report_data
    
    def _get_period_days(self, report_type: str) -> int:
        """レポートタイプから期間日数を取得"""
        if report_type == "daily":
            return 1
        elif report_type == "weekly":
            return 7
        elif report_type == "monthly":
            return 30
        else:
            return 7
    
    def _get_report_type_label(self, report_type: str) -> str:
        """レポートタイプのラベルを取得"""
        labels = {
            "daily": "日次",
            "weekly": "週次",
            "monthly": "月次"
        }
        return labels.get(report_type, "週次")
    
    def _get_period_string(self, report_type: str, start_date: datetime, end_date: datetime) -> str:
        """期間文字列を生成"""
        if report_type == "daily":
            return end_date.strftime("%Y年%m月%d日")
        elif report_type == "weekly":
            return f"{start_date.strftime('%Y年%m月%d日')} - {end_date.strftime('%m月%d日')}"
        elif report_type == "monthly":
            return end_date.strftime("%Y年%m月")
        else:
            return f"{start_date.strftime('%Y年%m月%d日')} - {end_date.strftime('%m月%d日')}"


# シングルトンインスタンス
report_generator = ReportGenerator()