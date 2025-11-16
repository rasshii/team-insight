"""
チームリポジトリ - チームデータアクセス層

このモジュールは、チームモデルに特化したデータアクセスメソッドを提供します。

主要機能：
1. チームの基本的なCRUD操作
2. メンバー情報を含むチーム取得（N+1問題対策）
3. ユーザーが所属するチーム一覧取得
4. チーム統計情報の取得
5. チームメンバーの管理

パフォーマンス最適化：
- joinedload()による関連データの効率的な取得
- サブクエリを活用した統計情報の集計
- N+1問題の回避

使用例：
    team_repo = TeamRepository(db)

    # メンバー情報を含めて取得
    team = team_repo.get_with_members(team_id=1)

    # ユーザーのチーム一覧
    teams = team_repo.get_user_teams(user_id=1)

    # チーム統計
    stats = team_repo.get_team_statistics(team_id=1)
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, and_

from app.models.team import Team, TeamMember, TeamRole
from app.models.user import User
from app.models.task import Task, TaskStatus
from app.repositories.base_repository import BaseRepository


class TeamRepository(BaseRepository[Team]):
    """
    チームリポジトリクラス

    チームモデルに対する専用のデータアクセスメソッドを提供します。
    BaseRepositoryの汎用メソッドに加え、チーム特有の検索・集計機能を実装。

    主要メソッド：
    - get_with_members: メンバー情報を含めて取得
    - get_user_teams: ユーザーのチーム一覧
    - get_team_statistics: チーム統計情報の取得
    - get_team_members: チームメンバーの取得
    - get_member: 特定のメンバー情報を取得

    リレーション最適化：
    - joinedload()による効率的な関連データ取得
    - サブクエリを活用した集計
    - N+1問題の完全回避
    """

    def __init__(self, db: Session):
        """
        TeamRepositoryの初期化

        Args:
            db (Session): SQLAlchemyのデータベースセッション
        """
        super().__init__(Team, db)

    def get_by_name(self, name: str) -> Optional[Team]:
        """
        チーム名でチームを検索

        チーム名は一意制約があるため、常に0件または1件のレコードを返します。

        Args:
            name (str): チーム名

        Returns:
            Optional[Team]: 見つかった場合はTeamインスタンス、見つからない場合はNone

        Example:
            >>> team = team_repo.get_by_name("開発チーム")
            >>> if team:
            ...     print(f"Team: {team.description}")

        Note:
            - チーム名は一意制約
            - インデックスによる高速検索
        """
        return self.db.query(Team).filter(Team.name == name).first()

    def get_with_members(self, team_id: int) -> Optional[Team]:
        """
        メンバー情報を含めてチームを取得（N+1問題対策）

        チーム情報とそのチームに所属するすべてのメンバー情報を
        1回のクエリで効率的に取得します。

        取得されるデータ：
        - チーム基本情報
        - TeamMember（中間テーブル）情報
        - User（メンバー）情報

        N+1問題対策：
        - joinedload()により、関連するTeamMemberとUserを事前ロード
        - 複数のSQLクエリを1つに集約
        - パフォーマンスの大幅な向上

        Args:
            team_id (int): チームID

        Returns:
            Optional[Team]:
                見つかった場合はメンバー情報を含むTeamインスタンス、
                見つからない場合はNone

        Example:
            >>> team = team_repo.get_with_members(1)
            >>> if team:
            ...     print(f"Team: {team.name}")
            ...     for member in team.members:
            ...         print(f"  {member.user.name} ({member.role})")

        Note:
            - team.membersとuserが事前ロード済み
            - 追加のクエリは発行されない（N+1問題なし）
        """
        return (
            self.db.query(Team)
            .options(joinedload(Team.members).joinedload(TeamMember.user))
            .filter(Team.id == team_id)
            .first()
        )

    def get_user_teams(self, user_id: int, skip: int = 0, limit: int = 100) -> List[Team]:
        """
        ユーザーが所属するチーム一覧を取得

        特定のユーザーが所属するすべてのチームを取得します。
        メンバー情報も効率的に取得されます。

        Args:
            user_id (int): ユーザーID
            skip (int, optional): スキップするレコード数。デフォルトは0
            limit (int, optional): 取得する最大レコード数。デフォルトは100

        Returns:
            List[Team]: ユーザーが所属するチームのリスト

        Example:
            >>> # ユーザーのチーム一覧を取得
            >>> teams = team_repo.get_user_teams(user_id=1)
            >>> for team in teams:
            ...     print(f"Team: {team.name}")

        Note:
            - TeamMember中間テーブル経由で効率的にJOIN
            - メンバー情報も事前ロード
        """
        return (
            self.db.query(Team)
            .join(TeamMember)
            .filter(TeamMember.user_id == user_id)
            .options(joinedload(Team.members).joinedload(TeamMember.user))
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_team_statistics(self, team_id: int) -> Dict[str, Any]:
        """
        チーム統計情報を取得

        チームのパフォーマンスを示す主要指標を算出します。
        効率的なクエリで複数の統計を一括取得します。

        算出される統計情報：
        1. メンバー数: チームに所属するメンバーの総数
        2. アクティブタスク数: 未完了（TODO / IN_PROGRESS）のタスク数
        3. 今月の完了タスク数: 当月に完了したタスクの数
        4. 効率性スコア: 完了率を0-100%で表現

        Args:
            team_id (int): チームID

        Returns:
            Dict[str, Any]: チーム統計情報
                {
                    "member_count": 5,                  # メンバー数
                    "active_tasks_count": 15,           # アクティブタスク数
                    "completed_tasks_this_month": 25,   # 今月の完了タスク数
                    "efficiency_score": 62.5            # 効率性スコア（%）
                }

        Example:
            >>> stats = team_repo.get_team_statistics(team_id=1)
            >>> print(f"Efficiency: {stats['efficiency_score']:.1f}%")

        Note:
            - サブクエリを活用した効率的な集計
            - 1回のクエリで複数の統計を取得
        """
        # チームメンバー数を集計
        member_count = self.db.query(func.count(TeamMember.id)).filter(TeamMember.team_id == team_id).scalar() or 0

        # チームメンバーのユーザーIDをサブクエリで取得
        member_user_ids = self.db.query(TeamMember.user_id).filter(TeamMember.team_id == team_id).subquery()

        # アクティブなタスク数を集計（TODO / IN_PROGRESS）
        active_tasks_count = (
            self.db.query(func.count(Task.id))
            .filter(Task.assignee_id.in_(member_user_ids), Task.status.in_([TaskStatus.TODO, TaskStatus.IN_PROGRESS]))
            .scalar()
            or 0
        )

        # 今月の開始日時を計算（月初0時0分0秒）
        start_of_month = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        # 今月完了したタスク数を集計
        completed_tasks_this_month = (
            self.db.query(func.count(Task.id))
            .filter(
                Task.assignee_id.in_(member_user_ids), Task.status == TaskStatus.CLOSED, Task.completed_date >= start_of_month
            )
            .scalar()
            or 0
        )

        # 効率性スコアの計算
        total_tasks = (completed_tasks_this_month or 0) + (active_tasks_count or 0)
        if total_tasks > 0:
            efficiency_score = round((completed_tasks_this_month or 0) / total_tasks * 100, 1)
        else:
            efficiency_score = 0.0

        return {
            "member_count": member_count,
            "active_tasks_count": active_tasks_count,
            "completed_tasks_this_month": completed_tasks_this_month,
            "efficiency_score": efficiency_score,
        }

    def get_team_members(self, team_id: int, role: Optional[TeamRole] = None) -> List[TeamMember]:
        """
        チームメンバーを取得

        指定されたチームのメンバー一覧を取得します。
        ロールでフィルタリングも可能です。

        Args:
            team_id (int): チームID
            role (Optional[TeamRole], optional):
                ロールでフィルタリング。Noneの場合は全メンバー

        Returns:
            List[TeamMember]: チームメンバーのリスト

        Example:
            >>> # 全メンバーを取得
            >>> members = team_repo.get_team_members(team_id=1)
            >>> for member in members:
            ...     print(f"{member.user.name} ({member.role})")

            >>> # チームリーダーのみ取得
            >>> leaders = team_repo.get_team_members(
            ...     team_id=1, role=TeamRole.TEAM_LEADER
            ... )

        Note:
            - ユーザー情報も効率的に取得（joinedload）
            - N+1問題なし
        """
        query = self.db.query(TeamMember).options(joinedload(TeamMember.user)).filter(TeamMember.team_id == team_id)

        # ロールでフィルタリング
        if role is not None:
            query = query.filter(TeamMember.role == role)

        return query.all()

    def get_member(self, team_id: int, user_id: int) -> Optional[TeamMember]:
        """
        特定のメンバー情報を取得

        チームIDとユーザーIDから特定のメンバー情報を取得します。

        Args:
            team_id (int): チームID
            user_id (int): ユーザーID

        Returns:
            Optional[TeamMember]:
                見つかった場合はTeamMemberインスタンス、見つからない場合はNone

        Example:
            >>> member = team_repo.get_member(team_id=1, user_id=2)
            >>> if member:
            ...     print(f"Role: {member.role}")

        Note:
            - ユーザー情報も効率的に取得（joinedload）
        """
        return (
            self.db.query(TeamMember)
            .options(joinedload(TeamMember.user))
            .filter(TeamMember.team_id == team_id, TeamMember.user_id == user_id)
            .first()
        )

    def is_member(self, team_id: int, user_id: int) -> bool:
        """
        ユーザーがチームメンバーかチェック

        Args:
            team_id (int): チームID
            user_id (int): ユーザーID

        Returns:
            bool: メンバーの場合True、そうでない場合False

        Example:
            >>> if team_repo.is_member(team_id=1, user_id=2):
            ...     print("User is a team member")

        Note:
            - EXISTS句による効率的なチェック
        """
        return self.db.query(
            self.db.query(TeamMember).filter(TeamMember.team_id == team_id, TeamMember.user_id == user_id).exists()
        ).scalar()

    def is_team_leader(self, team_id: int, user_id: int) -> bool:
        """
        ユーザーがチームリーダーかチェック

        Args:
            team_id (int): チームID
            user_id (int): ユーザーID

        Returns:
            bool: チームリーダーの場合True、そうでない場合False

        Example:
            >>> if team_repo.is_team_leader(team_id=1, user_id=2):
            ...     print("User is a team leader")

        Note:
            - EXISTS句による効率的なチェック
        """
        return self.db.query(
            self.db.query(TeamMember)
            .filter(TeamMember.team_id == team_id, TeamMember.user_id == user_id, TeamMember.role == TeamRole.TEAM_LEADER)
            .exists()
        ).scalar()

    def count_members(self, team_id: int) -> int:
        """
        チームメンバー数をカウント

        Args:
            team_id (int): チームID

        Returns:
            int: メンバー数

        Example:
            >>> member_count = team_repo.count_members(team_id=1)
            >>> print(f"Members: {member_count}")

        Note:
            - COUNT(*)による高速カウント
        """
        return self.db.query(func.count(TeamMember.id)).filter(TeamMember.team_id == team_id).scalar() or 0

    def count_team_leaders(self, team_id: int) -> int:
        """
        チームリーダーの数をカウント

        Args:
            team_id (int): チームID

        Returns:
            int: チームリーダー数

        Example:
            >>> leader_count = team_repo.count_team_leaders(team_id=1)
            >>> print(f"Team leaders: {leader_count}")

        Note:
            - チーム削除時などに最後のリーダーかチェックするために使用
        """
        return (
            self.db.query(func.count(TeamMember.id))
            .filter(TeamMember.team_id == team_id, TeamMember.role == TeamRole.TEAM_LEADER)
            .scalar()
            or 0
        )

    def get_members_performance(self, team_id: int) -> List[Dict[str, Any]]:
        """
        チームメンバーのパフォーマンスデータを取得

        各メンバーのタスク統計情報を集計します。

        集計される情報：
        - completed_tasks: 今月の完了タスク数
        - active_tasks: アクティブタスク数
        - last_month_completed: 先月の完了タスク数

        Args:
            team_id (int): チームID

        Returns:
            List[Dict[str, Any]]: メンバーごとのパフォーマンスデータ

        Example:
            >>> performance = team_repo.get_members_performance(team_id=1)
            >>> for data in performance:
            ...     print(f"{data['user_name']}: {data['completed_tasks']} tasks")

        Note:
            - 効率的なサブクエリを使用
            - 複数のメンバーでも高速
        """
        # チームメンバーを取得
        members = self.get_team_members(team_id)

        # 今月の開始日時
        start_of_month = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        # 先月の開始日時
        start_of_last_month = (start_of_month - timedelta(days=1)).replace(day=1)

        performance_data = []

        for member in members:
            # 完了したタスク数（今月）
            completed_tasks = (
                self.db.query(func.count(Task.id))
                .filter(
                    Task.assignee_id == member.user_id, Task.status == TaskStatus.CLOSED, Task.completed_date >= start_of_month
                )
                .scalar()
                or 0
            )

            # アクティブなタスク数
            active_tasks = (
                self.db.query(func.count(Task.id))
                .filter(Task.assignee_id == member.user_id, Task.status.in_([TaskStatus.TODO, TaskStatus.IN_PROGRESS]))
                .scalar()
                or 0
            )

            # 先月の完了タスク数
            last_month_completed = (
                self.db.query(func.count(Task.id))
                .filter(
                    Task.assignee_id == member.user_id,
                    Task.status == TaskStatus.CLOSED,
                    Task.completed_date >= start_of_last_month,
                    Task.completed_date < start_of_month,
                )
                .scalar()
                or 0
            )

            # 効率性スコア
            total_tasks = completed_tasks + active_tasks
            efficiency = int((completed_tasks / total_tasks * 100) if total_tasks > 0 else 0)

            # トレンドの判定
            if completed_tasks > last_month_completed:
                trend = "up"
            elif completed_tasks < last_month_completed:
                trend = "down"
            else:
                trend = "stable"

            performance_data.append(
                {
                    "member_id": member.id,
                    "user_id": member.user_id,
                    "user_name": member.user.name,
                    "role": member.role,
                    "completed_tasks": completed_tasks,
                    "active_tasks": active_tasks,
                    "efficiency": efficiency,
                    "trend": trend,
                    "last_month_completed": last_month_completed,
                }
            )

        return performance_data

    def get_task_distribution(self, team_id: int) -> Dict[str, Any]:
        """
        チームのタスク分配データを取得

        各メンバーのタスク数を集計し、分配状況を可視化するためのデータを提供します。

        Args:
            team_id (int): チームID

        Returns:
            Dict[str, Any]: タスク分配データ
                {
                    "labels": ["Alice", "Bob", ...],
                    "data": [10, 15, ...],
                    "backgroundColor": ["#3b82f6", ...]
                }

        Example:
            >>> distribution = team_repo.get_task_distribution(team_id=1)
            >>> print(distribution["labels"])  # ["Alice", "Bob"]
            >>> print(distribution["data"])    # [10, 15]

        Note:
            - チャート表示用のデータ形式
            - 各メンバーの全タスク数（完了・未完了含む）
        """
        # チームメンバーを取得
        members = self.get_team_members(team_id)

        distribution_data = {
            "labels": [],
            "data": [],
            "backgroundColor": [
                "#3b82f6",
                "#10b981",
                "#f59e0b",
                "#ef4444",
                "#8b5cf6",
                "#ec4899",
                "#06b6d4",
                "#84cc16",
                "#f97316",
                "#6366f1",
            ],
        }

        for member in members:
            # 各メンバーのタスク数を取得
            task_count = self.db.query(func.count(Task.id)).filter(Task.assignee_id == member.user_id).scalar() or 0

            distribution_data["labels"].append(member.user.name)
            distribution_data["data"].append(task_count)

        return distribution_data
