"""
プロジェクトリポジトリ - プロジェクトデータアクセス層

このモジュールは、プロジェクトモデルに特化したデータアクセスメソッドを提供します。

主要機能：
1. プロジェクトの基本的なCRUD操作
2. Backlog IDやプロジェクトキーによる検索
3. メンバー情報を含むプロジェクト取得（N+1問題対策）
4. ユーザーが所属するプロジェクト一覧取得
5. プロジェクト統計情報の取得

パフォーマンス最適化：
- joinedload()による関連データの効率的な取得
- インデックスを活用した高速検索
- N+1問題の回避

使用例：
    project_repo = ProjectRepository(db)

    # Backlog IDで検索
    project = project_repo.get_by_backlog_id(12345)

    # メンバー情報を含めて取得
    project = project_repo.get_with_members(project_id=1)

    # ユーザーのプロジェクト一覧
    projects = project_repo.get_user_projects(user_id=1)
"""

from typing import Optional, List
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func

from app.models.project import Project
from app.models.user import User
from app.repositories.base_repository import BaseRepository


class ProjectRepository(BaseRepository[Project]):
    """
    プロジェクトリポジトリクラス

    プロジェクトモデルに対する専用のデータアクセスメソッドを提供します。
    BaseRepositoryの汎用メソッドに加え、プロジェクト特有の検索・取得機能を実装。

    主要メソッド：
    - get_by_backlog_id: Backlog IDで検索
    - get_by_project_key: プロジェクトキーで検索
    - get_with_members: メンバー情報を含めて取得
    - get_with_tasks: タスク情報を含めて取得
    - get_user_projects: ユーザーのプロジェクト一覧
    - get_active_projects: アクティブなプロジェクトのみ取得

    リレーション最適化：
    - joinedload()による効率的な関連データ取得
    - N+1問題の完全回避
    """

    def __init__(self, db: Session):
        """
        ProjectRepositoryの初期化

        Args:
            db (Session): SQLAlchemyのデータベースセッション
        """
        super().__init__(Project, db)

    def get_by_backlog_id(self, backlog_id: int) -> Optional[Project]:
        """
        Backlog IDでプロジェクトを検索

        Backlogシステムから連携されたプロジェクトを識別するためのメソッドです。
        backlog_idは一意制約があり、高速な検索が可能です。

        Args:
            backlog_id (int): BacklogプロジェクトID

        Returns:
            Optional[Project]: 見つかった場合はProjectインスタンス、見つからない場合はNone

        Example:
            >>> project = project_repo.get_by_backlog_id(12345)
            >>> if project:
            ...     print(f"Backlog project: {project.name}")

        Note:
            - Backlog連携プロジェクトのみ保持
            - インデックスによる高速検索
        """
        return self.db.query(Project).filter(Project.backlog_id == backlog_id).first()

    def get_by_project_key(self, project_key: str) -> Optional[Project]:
        """
        プロジェクトキーでプロジェクトを検索

        プロジェクトキーは一意制約があり、プロジェクトを識別する主要な方法です。
        例: "TEAM-INSIGHT", "PROJECT-ABC"

        Args:
            project_key (str): プロジェクトキー

        Returns:
            Optional[Project]: 見つかった場合はProjectインスタンス、見つからない場合はNone

        Example:
            >>> project = project_repo.get_by_project_key("TEAM-INSIGHT")
            >>> if project:
            ...     print(f"Project: {project.name}")

        Note:
            - プロジェクトキーは一意制約
            - インデックスによる高速検索
            - 大文字小文字を区別する
        """
        return self.db.query(Project).filter(Project.project_key == project_key).first()

    def get_with_members(self, project_id: int) -> Optional[Project]:
        """
        メンバー情報を含めてプロジェクトを取得（N+1問題対策）

        プロジェクト情報とそのプロジェクトに所属するすべてのメンバー情報を
        1回のクエリで効率的に取得します。

        取得されるデータ：
        - プロジェクト基本情報
        - メンバー（User）情報

        N+1問題対策：
        - joinedload()により、関連するUserを事前ロード
        - 多対多のリレーション（project_members中間テーブル）も効率的に処理
        - 複数のSQLクエリを1つに集約

        Args:
            project_id (int): プロジェクトID

        Returns:
            Optional[Project]:
                見つかった場合はメンバー情報を含むProjectインスタンス、
                見つからない場合はNone

        Example:
            >>> project = project_repo.get_with_members(1)
            >>> if project:
            ...     print(f"Project: {project.name}")
            ...     for member in project.members:
            ...         print(f"  Member: {member.name}")

        Note:
            - project.membersが事前ロード済み
            - 追加のクエリは発行されない（N+1問題なし）
            - メンバー数が多い場合は、selectinload()の使用も検討
        """
        return self.db.query(Project).options(joinedload(Project.members)).filter(Project.id == project_id).first()

    def get_with_tasks(self, project_id: int, task_limit: Optional[int] = None) -> Optional[Project]:
        """
        タスク情報を含めてプロジェクトを取得（N+1問題対策）

        プロジェクト情報とそのプロジェクトに紐づくタスク情報を
        効率的に取得します。

        Args:
            project_id (int): プロジェクトID
            task_limit (Optional[int], optional):
                取得するタスクの最大数。Noneの場合は全件取得。

        Returns:
            Optional[Project]:
                見つかった場合はタスク情報を含むProjectインスタンス、
                見つからない場合はNone

        Example:
            >>> # 最新の100件のタスクを含めて取得
            >>> project = project_repo.get_with_tasks(1, task_limit=100)
            >>> if project:
            ...     for task in project.tasks:
            ...         print(f"  Task: {task.title}")

        Note:
            - project.tasksが事前ロード済み
            - タスク数が多い場合はtask_limitで制限推奨
            - selectinload()を使用してコレクションを効率的に取得
        """
        from sqlalchemy.orm import selectinload

        query = self.db.query(Project).options(selectinload(Project.tasks)).filter(Project.id == project_id)

        return query.first()

    def get_user_projects(self, user_id: int, skip: int = 0, limit: int = 100) -> List[Project]:
        """
        ユーザーが所属するプロジェクト一覧を取得

        多対多のリレーション（project_members中間テーブル）を使用して、
        特定のユーザーが所属するすべてのプロジェクトを取得します。

        取得されるプロジェクト：
        - ユーザーがメンバーとして登録されているプロジェクト
        - ページネーション対応

        Args:
            user_id (int): ユーザーID
            skip (int, optional): スキップするレコード数。デフォルトは0
            limit (int, optional): 取得する最大レコード数。デフォルトは100

        Returns:
            List[Project]: ユーザーが所属するプロジェクトのリスト

        Example:
            >>> # ユーザーのプロジェクト一覧を取得
            >>> projects = project_repo.get_user_projects(user_id=1)
            >>> for project in projects:
            ...     print(f"Project: {project.name}")

            >>> # ページネーション
            >>> projects = project_repo.get_user_projects(
            ...     user_id=1, skip=10, limit=10
            ... )

        Note:
            - 中間テーブル経由の効率的なJOIN
            - ユーザー情報は含まれない（必要に応じてjoinedloadを追加）
        """
        return self.db.query(Project).join(Project.members).filter(User.id == user_id).offset(skip).limit(limit).all()

    def get_active_projects(self, skip: int = 0, limit: int = 100) -> List[Project]:
        """
        アクティブなプロジェクトのみを取得

        status='active'のプロジェクトのみをフィルタリングして取得します。
        ページネーション対応で、大量データでも効率的に処理可能です。

        Args:
            skip (int, optional): スキップするレコード数。デフォルトは0
            limit (int, optional): 取得する最大レコード数。デフォルトは100

        Returns:
            List[Project]: アクティブなプロジェクトのリスト

        Example:
            >>> # 最初の20件のアクティブプロジェクトを取得
            >>> active_projects = project_repo.get_active_projects(
            ...     skip=0, limit=20
            ... )
            >>> print(f"Active projects: {len(active_projects)}")

        Note:
            - statusカラムにインデックスがあれば高速
            - アーカイブされたプロジェクトは除外される
        """
        return self.db.query(Project).filter(Project.status == "active").offset(skip).limit(limit).all()

    def get_projects_with_stats(self, skip: int = 0, limit: int = 100) -> List[Project]:
        """
        統計情報を含むプロジェクト一覧を取得

        各プロジェクトにタスク数やメンバー数などの統計情報を付加して取得します。
        サブクエリを使用して効率的に集計を行います。

        付加される統計情報：
        - task_count: タスク数
        - member_count: メンバー数

        Args:
            skip (int, optional): スキップするレコード数。デフォルトは0
            limit (int, optional): 取得する最大レコード数。デフォルトは100

        Returns:
            List[Project]: 統計情報が付加されたプロジェクトのリスト

        Example:
            >>> projects = project_repo.get_projects_with_stats(limit=10)
            >>> for project in projects:
            ...     print(f"{project.name}: {project.task_count} tasks, "
            ...           f"{project.member_count} members")

        Note:
            - サブクエリによる効率的な集計
            - 結果のProjectインスタンスにはtask_count、member_countが動的に追加される
        """
        from app.models.task import Task
        from app.models.project import project_members

        # タスク数のサブクエリ
        task_count_subq = (
            self.db.query(Task.project_id, func.count(Task.id).label("task_count")).group_by(Task.project_id).subquery()
        )

        # メンバー数のサブクエリ
        member_count_subq = (
            self.db.query(project_members.c.project_id, func.count(project_members.c.user_id).label("member_count"))
            .group_by(project_members.c.project_id)
            .subquery()
        )

        # プロジェクトと統計情報をJOIN
        projects = (
            self.db.query(
                Project,
                func.coalesce(task_count_subq.c.task_count, 0).label("task_count"),
                func.coalesce(member_count_subq.c.member_count, 0).label("member_count"),
            )
            .outerjoin(task_count_subq, Project.id == task_count_subq.c.project_id)
            .outerjoin(member_count_subq, Project.id == member_count_subq.c.project_id)
            .offset(skip)
            .limit(limit)
            .all()
        )

        # 結果を整形（統計情報をProjectインスタンスに追加）
        result = []
        for project, task_count, member_count in projects:
            project.task_count = task_count
            project.member_count = member_count
            result.append(project)

        return result

    def count_user_projects(self, user_id: int) -> int:
        """
        ユーザーが所属するプロジェクト数をカウント

        Args:
            user_id (int): ユーザーID

        Returns:
            int: ユーザーが所属するプロジェクト数

        Example:
            >>> project_count = project_repo.count_user_projects(user_id=1)
            >>> print(f"User belongs to {project_count} projects")

        Note:
            - COUNT(*)による高速カウント
            - 中間テーブル経由でカウント
        """
        return self.db.query(func.count(Project.id)).join(Project.members).filter(User.id == user_id).scalar() or 0

    def add_member(self, project_id: int, user_id: int) -> bool:
        """
        プロジェクトにメンバーを追加

        project_members中間テーブルにレコードを追加して、
        ユーザーをプロジェクトメンバーとして登録します。

        Args:
            project_id (int): プロジェクトID
            user_id (int): ユーザーID

        Returns:
            bool: 追加成功時はTrue、既に存在する場合や失敗時はFalse

        Example:
            >>> if project_repo.add_member(project_id=1, user_id=2):
            ...     print("Member added successfully")

        Note:
            - 既に存在する場合は何もせずFalseを返す
            - db.commit()は呼び出し側で実行
        """
        from app.models.project import project_members

        # 既に存在するかチェック
        exists = (
            self.db.query(project_members)
            .filter(project_members.c.project_id == project_id, project_members.c.user_id == user_id)
            .first()
        )

        if exists:
            return False

        # 中間テーブルにINSERT
        self.db.execute(project_members.insert().values(project_id=project_id, user_id=user_id))
        self.db.flush()

        return True

    def remove_member(self, project_id: int, user_id: int) -> bool:
        """
        プロジェクトからメンバーを削除

        project_members中間テーブルからレコードを削除して、
        ユーザーをプロジェクトメンバーから除外します。

        Args:
            project_id (int): プロジェクトID
            user_id (int): ユーザーID

        Returns:
            bool: 削除成功時はTrue、存在しない場合や失敗時はFalse

        Example:
            >>> if project_repo.remove_member(project_id=1, user_id=2):
            ...     print("Member removed successfully")

        Note:
            - 存在しない場合は何もせずFalseを返す
            - db.commit()は呼び出し側で実行
        """
        from app.models.project import project_members

        # 中間テーブルからDELETE
        result = self.db.execute(
            project_members.delete().where(project_members.c.project_id == project_id, project_members.c.user_id == user_id)
        )
        self.db.flush()

        # 削除された行数をチェック
        return result.rowcount > 0
