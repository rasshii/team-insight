"""
チーム管理サービス
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import IntegrityError
from sqlalchemy import func, and_

from app.models.team import Team, TeamMember, TeamRole
from app.models.user import User
from app.models.task import Task, TaskStatus
from app.schemas.team import TeamCreate, TeamUpdate, TeamMemberCreate
from app.core.exceptions import (
    NotFoundException,
    ConflictException,
    ValidationException
)

import logging

logger = logging.getLogger(__name__)


class TeamService:
    """チーム管理サービス"""
    
    def get_teams(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 100,
        with_stats: bool = False
    ) -> Dict[str, Any]:
        """
        チーム一覧を取得
        
        Args:
            db: データベースセッション
            skip: スキップ数
            limit: 取得件数上限
            with_stats: 統計情報を含むかどうか
            
        Returns:
            チーム一覧と総数
        """
        query = db.query(Team).options(
            joinedload(Team.members).joinedload(TeamMember.user)
        )
        
        total = query.count()
        teams = query.offset(skip).limit(limit).all()
        
        if with_stats:
            # 統計情報を追加
            for team in teams:
                team_stats = self._calculate_team_stats(db, team.id)
                team.member_count = team_stats["member_count"]
                team.active_tasks_count = team_stats["active_tasks_count"]
                team.completed_tasks_this_month = team_stats["completed_tasks_this_month"]
                team.efficiency_score = team_stats["efficiency_score"]
        
        return {
            "teams": teams,
            "total": total
        }
    
    def get_team(
        self,
        db: Session,
        team_id: int,
        with_stats: bool = True
    ) -> Team:
        """
        チーム詳細を取得
        
        Args:
            db: データベースセッション
            team_id: チームID
            with_stats: 統計情報を含むかどうか
            
        Returns:
            チーム情報
            
        Raises:
            NotFoundException: チームが見つからない場合
        """
        team = db.query(Team).options(
            joinedload(Team.members).joinedload(TeamMember.user)
        ).filter(Team.id == team_id).first()
        
        if not team:
            raise NotFoundException(f"チーム (ID: {team_id}) が見つかりません")
        
        if with_stats:
            team_stats = self._calculate_team_stats(db, team.id)
            team.member_count = team_stats["member_count"]
            team.active_tasks_count = team_stats["active_tasks_count"]
            team.completed_tasks_this_month = team_stats["completed_tasks_this_month"]
            team.efficiency_score = team_stats["efficiency_score"]
        
        return team
    
    def create_team(
        self,
        db: Session,
        team_data: TeamCreate,
        creator_user_id: int
    ) -> Team:
        """
        チームを作成
        
        Args:
            db: データベースセッション
            team_data: チーム作成データ
            creator_user_id: 作成者のユーザーID
            
        Returns:
            作成されたチーム
            
        Raises:
            ConflictException: 同名のチームが既に存在する場合
        """
        # 同名チームの存在確認
        existing = db.query(Team).filter(
            Team.name == team_data.name
        ).first()
        
        if existing:
            raise ConflictException(f"チーム名 '{team_data.name}' は既に使用されています")
        
        try:
            # チーム作成
            team = Team(**team_data.model_dump())
            db.add(team)
            db.flush()
            
            # 作成者をチームリーダーとして追加
            creator_member = TeamMember(
                team_id=team.id,
                user_id=creator_user_id,
                role=TeamRole.TEAM_LEADER
            )
            db.add(creator_member)
            
            db.commit()
            db.refresh(team)
            
            logger.info(f"Team created: {team.name} (ID: {team.id}) by user {creator_user_id}")
            
            return self.get_team(db, team.id)
            
        except IntegrityError as e:
            db.rollback()
            logger.error(f"Failed to create team: {str(e)}")
            raise ConflictException("チームの作成に失敗しました")
    
    def update_team(
        self,
        db: Session,
        team_id: int,
        team_data: TeamUpdate
    ) -> Team:
        """
        チームを更新
        
        Args:
            db: データベースセッション
            team_id: チームID
            team_data: チーム更新データ
            
        Returns:
            更新されたチーム
            
        Raises:
            NotFoundException: チームが見つからない場合
            ConflictException: 同名のチームが既に存在する場合
        """
        team = db.query(Team).filter(Team.id == team_id).first()
        
        if not team:
            raise NotFoundException(f"チーム (ID: {team_id}) が見つかりません")
        
        # 名前の重複チェック
        if team_data.name and team_data.name != team.name:
            existing = db.query(Team).filter(
                Team.name == team_data.name,
                Team.id != team_id
            ).first()
            
            if existing:
                raise ConflictException(f"チーム名 '{team_data.name}' は既に使用されています")
        
        # 更新
        update_data = team_data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(team, key, value)
        
        team.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(team)
        
        logger.info(f"Team updated: {team.name} (ID: {team.id})")
        
        return self.get_team(db, team.id)
    
    def delete_team(
        self,
        db: Session,
        team_id: int
    ) -> None:
        """
        チームを削除
        
        Args:
            db: データベースセッション
            team_id: チームID
            
        Raises:
            NotFoundException: チームが見つからない場合
        """
        team = db.query(Team).filter(Team.id == team_id).first()
        
        if not team:
            raise NotFoundException(f"チーム (ID: {team_id}) が見つかりません")
        
        # カスケード削除でメンバーも削除される
        db.delete(team)
        db.commit()
        
        logger.info(f"Team deleted: {team.name} (ID: {team.id})")
    
    def add_member(
        self,
        db: Session,
        team_id: int,
        member_data: TeamMemberCreate
    ) -> TeamMember:
        """
        チームにメンバーを追加
        
        Args:
            db: データベースセッション
            team_id: チームID
            member_data: メンバー追加データ
            
        Returns:
            追加されたメンバー情報
            
        Raises:
            NotFoundException: チームまたはユーザーが見つからない場合
            ConflictException: 既にメンバーの場合
        """
        # チームの存在確認
        team = db.query(Team).filter(Team.id == team_id).first()
        if not team:
            raise NotFoundException(f"チーム (ID: {team_id}) が見つかりません")
        
        # ユーザーの存在確認
        user = db.query(User).filter(User.id == member_data.user_id).first()
        if not user:
            raise NotFoundException(f"ユーザー (ID: {member_data.user_id}) が見つかりません")
        
        # 既存メンバーチェック
        existing = db.query(TeamMember).filter(
            TeamMember.team_id == team_id,
            TeamMember.user_id == member_data.user_id
        ).first()
        
        if existing:
            raise ConflictException(f"ユーザー {user.name} は既にチームメンバーです")
        
        # メンバー追加
        member = TeamMember(
            team_id=team_id,
            user_id=member_data.user_id,
            role=member_data.role
        )
        db.add(member)
        db.commit()
        db.refresh(member)
        
        # 関連データをロード
        member = db.query(TeamMember).options(
            joinedload(TeamMember.user)
        ).filter(TeamMember.id == member.id).first()
        
        logger.info(f"Member added to team: user {user.name} to team {team.name}")
        
        return member
    
    def update_member_role(
        self,
        db: Session,
        team_id: int,
        user_id: int,
        new_role: TeamRole
    ) -> TeamMember:
        """
        メンバーの役割を更新
        
        Args:
            db: データベースセッション
            team_id: チームID
            user_id: ユーザーID
            new_role: 新しい役割
            
        Returns:
            更新されたメンバー情報
            
        Raises:
            NotFoundException: メンバーが見つからない場合
        """
        member = db.query(TeamMember).filter(
            TeamMember.team_id == team_id,
            TeamMember.user_id == user_id
        ).first()
        
        if not member:
            raise NotFoundException("チームメンバーが見つかりません")
        
        member.role = new_role
        member.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(member)
        
        # 関連データをロード
        member = db.query(TeamMember).options(
            joinedload(TeamMember.user)
        ).filter(TeamMember.id == member.id).first()
        
        logger.info(f"Member role updated: user {user_id} in team {team_id} to {new_role}")
        
        return member
    
    def remove_member(
        self,
        db: Session,
        team_id: int,
        user_id: int
    ) -> None:
        """
        チームからメンバーを削除
        
        Args:
            db: データベースセッション
            team_id: チームID
            user_id: ユーザーID
            
        Raises:
            NotFoundException: メンバーが見つからない場合
            ValidationException: 最後のチームリーダーを削除しようとした場合
        """
        member = db.query(TeamMember).filter(
            TeamMember.team_id == team_id,
            TeamMember.user_id == user_id
        ).first()
        
        if not member:
            raise NotFoundException("チームメンバーが見つかりません")
        
        # 最後のチームリーダーかチェック
        if member.role == TeamRole.TEAM_LEADER:
            leader_count = db.query(func.count(TeamMember.id)).filter(
                TeamMember.team_id == team_id,
                TeamMember.role == TeamRole.TEAM_LEADER
            ).scalar()
            
            if leader_count <= 1:
                raise ValidationException("最後のチームリーダーは削除できません")
        
        db.delete(member)
        db.commit()
        
        logger.info(f"Member removed from team: user {user_id} from team {team_id}")
    
    def get_user_teams(
        self,
        db: Session,
        user_id: int
    ) -> List[Team]:
        """
        ユーザーが所属するチーム一覧を取得
        
        Args:
            db: データベースセッション
            user_id: ユーザーID
            
        Returns:
            チーム一覧
        """
        teams = db.query(Team).join(TeamMember).filter(
            TeamMember.user_id == user_id
        ).options(
            joinedload(Team.members).joinedload(TeamMember.user)
        ).all()
        
        return teams
    
    def _calculate_team_stats(
        self,
        db: Session,
        team_id: int
    ) -> Dict[str, Any]:
        """
        チームの統計情報を計算
        
        Args:
            db: データベースセッション
            team_id: チームID
            
        Returns:
            統計情報の辞書
        """
        # メンバー数
        member_count = db.query(func.count(TeamMember.id)).filter(
            TeamMember.team_id == team_id
        ).scalar()
        
        # チームメンバーのユーザーIDリスト
        member_user_ids = db.query(TeamMember.user_id).filter(
            TeamMember.team_id == team_id
        ).subquery()
        
        # アクティブなタスク数
        active_tasks_count = db.query(func.count(Task.id)).filter(
            Task.assignee_id.in_(member_user_ids),
            Task.status.in_([TaskStatus.TODO, TaskStatus.IN_PROGRESS])
        ).scalar()
        
        # 今月完了したタスク数
        start_of_month = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        completed_tasks_this_month = db.query(func.count(Task.id)).filter(
            Task.assignee_id.in_(member_user_ids),
            Task.status == TaskStatus.CLOSED,
            Task.completed_date >= start_of_month
        ).scalar()
        
        # 効率性スコアの計算
        # 完了タスク数 / (完了タスク数 + アクティブタスク数) * 100
        total_tasks = (completed_tasks_this_month or 0) + (active_tasks_count or 0)
        if total_tasks > 0:
            efficiency_score = round((completed_tasks_this_month or 0) / total_tasks * 100, 1)
        else:
            efficiency_score = 0.0
        
        return {
            "member_count": member_count or 0,
            "active_tasks_count": active_tasks_count or 0,
            "completed_tasks_this_month": completed_tasks_this_month or 0,
            "efficiency_score": efficiency_score
        }
    
    def get_members_performance(
        self,
        db: Session,
        team_id: int
    ) -> List[Dict[str, Any]]:
        """
        チームメンバーのパフォーマンスデータを取得
        
        Args:
            db: データベースセッション
            team_id: チームID
            
        Returns:
            メンバーごとのパフォーマンスデータ
        """
        # チームメンバーを取得
        members = db.query(TeamMember).filter(
            TeamMember.team_id == team_id
        ).options(
            joinedload(TeamMember.user)
        ).all()
        
        performance_data = []
        start_of_month = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        for member in members:
            # 完了したタスク数（今月）
            completed_tasks = db.query(func.count(Task.id)).filter(
                Task.assignee_id == member.user_id,
                Task.status == TaskStatus.CLOSED,
                Task.completed_date >= start_of_month
            ).scalar() or 0
            
            # アクティブなタスク数
            active_tasks = db.query(func.count(Task.id)).filter(
                Task.assignee_id == member.user_id,
                Task.status.in_([TaskStatus.TODO, TaskStatus.IN_PROGRESS])
            ).scalar() or 0
            
            # 効率性スコア（完了タスク / (完了タスク + アクティブタスク) * 100）
            total_tasks = completed_tasks + active_tasks
            efficiency = int((completed_tasks / total_tasks * 100) if total_tasks > 0 else 0)
            
            # 前月のデータと比較してトレンドを計算
            start_of_last_month = (start_of_month - timedelta(days=1)).replace(day=1)
            last_month_completed = db.query(func.count(Task.id)).filter(
                Task.assignee_id == member.user_id,
                Task.status == TaskStatus.CLOSED,
                Task.completed_date >= start_of_last_month,
                Task.completed_date < start_of_month
            ).scalar() or 0
            
            # トレンドの判定
            if completed_tasks > last_month_completed:
                trend = 'up'
            elif completed_tasks < last_month_completed:
                trend = 'down'
            else:
                trend = 'stable'
            
            performance_data.append({
                "member_id": member.id,
                "user_id": member.user_id,
                "user_name": member.user.name,
                "role": member.role,
                "completed_tasks": completed_tasks,
                "active_tasks": active_tasks,
                "efficiency": efficiency,
                "trend": trend,
                "last_month_completed": last_month_completed
            })
        
        return performance_data
    
    def get_task_distribution(
        self,
        db: Session,
        team_id: int
    ) -> Dict[str, Any]:
        """
        チームのタスク分配データを取得
        
        Args:
            db: データベースセッション
            team_id: チームID
            
        Returns:
            タスク分配データ
        """
        # チームメンバーを取得
        members = db.query(TeamMember).filter(
            TeamMember.team_id == team_id
        ).options(
            joinedload(TeamMember.user)
        ).all()
        
        distribution_data = {
            "labels": [],
            "data": [],
            "backgroundColor": [
                "#3b82f6", "#10b981", "#f59e0b", "#ef4444", "#8b5cf6",
                "#ec4899", "#06b6d4", "#84cc16", "#f97316", "#6366f1"
            ]
        }
        
        for i, member in enumerate(members):
            # 各メンバーのタスク数を取得
            task_count = db.query(func.count(Task.id)).filter(
                Task.assignee_id == member.user_id
            ).scalar() or 0
            
            distribution_data["labels"].append(member.user.name)
            distribution_data["data"].append(task_count)
        
        return distribution_data
    
    def get_productivity_trend(
        self,
        db: Session,
        team_id: int,
        period: str = "monthly"
    ) -> List[Dict[str, Any]]:
        """
        チームの生産性推移データを取得
        
        Args:
            db: データベースセッション
            team_id: チームID
            period: 期間（daily, weekly, monthly）
            
        Returns:
            生産性推移データ
        """
        # チームメンバーのユーザーIDリストを取得
        member_user_ids = db.query(TeamMember.user_id).filter(
            TeamMember.team_id == team_id
        ).all()
        member_user_ids = [uid[0] for uid in member_user_ids]
        
        if not member_user_ids:
            return []
        
        # 期間の設定
        now = datetime.now()
        if period == "daily":
            start_date = now - timedelta(days=30)
            date_format = 'YYYY-MM-DD'
            date_trunc = 'day'
        elif period == "weekly":
            start_date = now - timedelta(weeks=12)
            date_format = 'YYYY-"W"IW'
            date_trunc = 'week'
        else:  # monthly
            start_date = now - timedelta(days=365)
            date_format = 'YYYY-MM'
            date_trunc = 'month'
        
        # タスクの完了データを取得
        completed_tasks = db.query(
            func.date_trunc(date_trunc, Task.completed_date).label('period_date'),
            func.count(Task.id).label('completed_count'),
            func.avg(
                func.extract('epoch', Task.completed_date - Task.created_at) / 86400
            ).label('avg_completion_days')
        ).filter(
            Task.assignee_id.in_(member_user_ids),
            Task.status == TaskStatus.CLOSED,
            Task.completed_date >= start_date,
            Task.completed_date.isnot(None)
        ).group_by(
            func.date_trunc(date_trunc, Task.completed_date)
        ).all()
        
        # 期間ごとのデータを作成
        period_data = {}
        for task in completed_tasks:
            period_key = task.period_date.strftime({
                'day': '%Y-%m-%d',
                'week': '%Y-W%V',
                'month': '%Y-%m'
            }[date_trunc])
            
            period_data[period_key] = {
                "period": period_key,
                "completed_tasks": task.completed_count,
                "avg_completion_time": round(task.avg_completion_days, 1) if task.avg_completion_days else 0,
                "efficiency_score": min(100, int(100 / (task.avg_completion_days + 1))) if task.avg_completion_days else 0
            }
        
        # 全期間のデータを生成（データがない期間も含む）
        trend_data = []
        current_date = start_date
        while current_date <= now:
            if period == "daily":
                period_key = current_date.strftime('%Y-%m-%d')
                current_date += timedelta(days=1)
            elif period == "weekly":
                period_key = current_date.strftime('%Y-W%V')
                current_date += timedelta(weeks=1)
            else:  # monthly
                period_key = current_date.strftime('%Y-%m')
                # 次の月の初日に移動
                if current_date.month == 12:
                    current_date = current_date.replace(year=current_date.year + 1, month=1, day=1)
                else:
                    current_date = current_date.replace(month=current_date.month + 1, day=1)
            
            if period_key in period_data:
                trend_data.append(period_data[period_key])
            else:
                trend_data.append({
                    "period": period_key,
                    "completed_tasks": 0,
                    "avg_completion_time": 0,
                    "efficiency_score": 0
                })
        
        return trend_data
    
    def get_team_activities(
        self,
        db: Session,
        team_id: int,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        チームの最近のアクティビティを取得
        
        Args:
            db: データベースセッション
            team_id: チームID
            limit: 取得件数
            
        Returns:
            アクティビティリスト
        """
        # チームメンバーのユーザーIDリストを取得
        member_user_ids = db.query(TeamMember.user_id).filter(
            TeamMember.team_id == team_id
        ).all()
        member_user_ids = [uid[0] for uid in member_user_ids]
        
        # 最近のタスク更新を取得
        tasks = db.query(Task).filter(
            Task.assignee_id.in_(member_user_ids)
        ).order_by(
            Task.updated_at.desc()
        ).limit(limit).all()
        
        activities = []
        for task in tasks:
            # タスクの担当者を取得
            assignee = db.query(User).filter(User.id == task.assignee_id).first()
            
            # アクティビティタイプを判定
            if task.status == TaskStatus.CLOSED and task.completed_date:
                activity_type = "completed"
                message = f"{assignee.name}さんがタスクを完了しました"
            elif task.status == TaskStatus.IN_PROGRESS:
                activity_type = "in_progress"
                message = f"{assignee.name}さんがタスクを開始しました"
            elif task.created_at == task.updated_at:
                activity_type = "created"
                message = f"{assignee.name}さんに新しいタスクが割り当てられました"
            else:
                activity_type = "updated"
                message = f"{assignee.name}さんのタスクが更新されました"
            
            activities.append({
                "id": f"task-{task.id}",
                "type": activity_type,
                "message": message,
                "title": task.title,
                "user": {
                    "id": assignee.id,
                    "name": assignee.name
                },
                "timestamp": task.updated_at.isoformat(),
                "status": task.status
            })
        
        return activities


team_service = TeamService()