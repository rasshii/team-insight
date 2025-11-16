"""
ユーザーリポジトリ - ユーザーデータアクセス層

このモジュールは、ユーザーモデルに特化したデータアクセスメソッドを提供します。

主要機能：
1. ユーザーの基本的なCRUD操作
2. メールアドレスやBacklog IDによる検索
3. ロール情報を含むユーザー取得（N+1問題対策）
4. ユーザー検索（名前、メール）
5. アクティブユーザーのフィルタリング

パフォーマンス最適化：
- joinedload()による関連データの効率的な取得
- インデックスを活用した高速検索
- N+1問題の回避

使用例：
    user_repo = UserRepository(db)

    # メールアドレスで検索
    user = user_repo.get_by_email("user@example.com")

    # ロール情報を含めて取得
    user_with_roles = user_repo.get_with_roles(user_id=1)

    # ユーザー検索
    users = user_repo.search(query="田中")
"""

from typing import Optional, List
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_, and_

from app.models.user import User
from app.models.rbac import UserRole, Role
from app.repositories.base_repository import BaseRepository


class UserRepository(BaseRepository[User]):
    """
    ユーザーリポジトリクラス

    ユーザーモデルに対する専用のデータアクセスメソッドを提供します。
    BaseRepositoryの汎用メソッドに加え、ユーザー特有の検索・取得機能を実装。

    主要メソッド：
    - get_by_email: メールアドレスで検索
    - get_by_backlog_id: Backlog IDで検索
    - get_by_user_id: ユーザーID（文字列）で検索
    - get_with_roles: ロール情報を含めて取得
    - get_active_users: アクティブなユーザーのみ取得
    - search: ユーザー検索（名前、メール）

    リレーション最適化：
    - joinedload()による効率的な関連データ取得
    - selectinload()によるコレクションの最適化
    - N+1問題の完全回避
    """

    def __init__(self, db: Session):
        """
        UserRepositoryの初期化

        Args:
            db (Session): SQLAlchemyのデータベースセッション
        """
        super().__init__(User, db)

    def get_by_email(self, email: str) -> Optional[User]:
        """
        メールアドレスでユーザーを検索

        メールアドレスは一意制約があるため、常に0件または1件のレコードを返します。
        インデックスが効くため、高速な検索が可能です。

        Args:
            email (str): 検索するメールアドレス

        Returns:
            Optional[User]: 見つかった場合はUserインスタンス、見つからない場合はNone

        Example:
            >>> user = user_repo.get_by_email("user@example.com")
            >>> if user:
            ...     print(f"Found user: {user.name}")

        Note:
            - メールアドレスは一意制約があるため、必ず0件または1件
            - インデックスによる高速検索
        """
        return self.db.query(User).filter(User.email == email).first()

    def get_by_backlog_id(self, backlog_id: int) -> Optional[User]:
        """
        Backlog IDでユーザーを検索

        Backlogシステムから連携されたユーザーを識別するためのメソッドです。
        backlog_idは一意制約があり、高速な検索が可能です。

        Args:
            backlog_id (int): BacklogユーザーID

        Returns:
            Optional[User]: 見つかった場合はUserインスタンス、見つからない場合はNone

        Example:
            >>> user = user_repo.get_by_backlog_id(12345)
            >>> if user:
            ...     print(f"Backlog user: {user.name}")

        Note:
            - Backlog連携ユーザーのみ保持
            - インデックスによる高速検索
        """
        return self.db.query(User).filter(User.backlog_id == backlog_id).first()

    def get_by_user_id(self, user_id: str) -> Optional[User]:
        """
        ユーザーID（文字列）でユーザーを検索

        Backlogのユーザー識別子（文字列形式）でユーザーを検索します。
        user_idは一意制約があり、インデックスが効くため高速です。

        Args:
            user_id (str): Backlogユーザー識別子（文字列）

        Returns:
            Optional[User]: 見つかった場合はUserインスタンス、見つからない場合はNone

        Example:
            >>> user = user_repo.get_by_user_id("user123")
            >>> if user:
            ...     print(f"User: {user.name}")

        Note:
            - Backlogの文字列形式ユーザーID
            - インデックスによる高速検索
        """
        return self.db.query(User).filter(User.user_id == user_id).first()

    def get_with_roles(self, user_id: int) -> Optional[User]:
        """
        ロール情報を含めてユーザーを取得（N+1問題対策）

        ユーザー情報とそのユーザーが持つすべてのロール情報を
        1回のクエリで効率的に取得します。

        取得されるデータ：
        - ユーザー基本情報
        - UserRole（ユーザーとロールの中間テーブル）
        - Role（ロール情報）

        N+1問題対策：
        - joinedload()により、関連するUserRoleとRoleを事前ロード
        - 複数のSQLクエリを1つに集約
        - パフォーマンスの大幅な向上

        Args:
            user_id (int): ユーザーID

        Returns:
            Optional[User]:
                見つかった場合はロール情報を含むUserインスタンス、
                見つからない場合はNone

        Example:
            >>> user = user_repo.get_with_roles(1)
            >>> if user:
            ...     for user_role in user.user_roles:
            ...         print(f"Role: {user_role.role.name}")
            ...         if user_role.project_id:
            ...             print(f"  Project ID: {user_role.project_id}")

        Note:
            - user.user_rolesとroleが事前ロード済み
            - 追加のクエリは発行されない（N+1問題なし）
            - 管理者権限チェック（is_admin）も効率的に実行可能
        """
        return (
            self.db.query(User)
            .options(joinedload(User.user_roles).joinedload(UserRole.role))
            .filter(User.id == user_id)
            .first()
        )

    def get_with_projects(self, user_id: int) -> Optional[User]:
        """
        プロジェクト情報を含めてユーザーを取得（N+1問題対策）

        ユーザー情報とそのユーザーが所属するすべてのプロジェクト情報を
        1回のクエリで効率的に取得します。

        Args:
            user_id (int): ユーザーID

        Returns:
            Optional[User]:
                見つかった場合はプロジェクト情報を含むUserインスタンス、
                見つからない場合はNone

        Example:
            >>> user = user_repo.get_with_projects(1)
            >>> if user:
            ...     for project in user.projects:
            ...         print(f"Project: {project.name}")

        Note:
            - user.projectsが事前ロード済み
            - 多対多のリレーションも効率的に取得
        """
        return self.db.query(User).options(joinedload(User.projects)).filter(User.id == user_id).first()

    def get_active_users(self, skip: int = 0, limit: int = 100) -> List[User]:
        """
        アクティブなユーザーのみを取得

        is_active=Trueのユーザーのみをフィルタリングして取得します。
        ページネーション対応で、大量データでも効率的に処理可能です。

        Args:
            skip (int, optional): スキップするレコード数。デフォルトは0
            limit (int, optional): 取得する最大レコード数。デフォルトは100

        Returns:
            List[User]: アクティブなユーザーのリスト

        Example:
            >>> # 最初の20件のアクティブユーザーを取得
            >>> active_users = user_repo.get_active_users(skip=0, limit=20)
            >>> print(f"Active users: {len(active_users)}")

        Note:
            - is_activeカラムにインデックスがあれば高速
            - 大量データの場合は適切なlimitを設定
        """
        return self.db.query(User).filter(User.is_active == True).offset(skip).limit(limit).all()

    def search(self, query: str, skip: int = 0, limit: int = 100) -> List[User]:
        """
        ユーザー検索（名前、メールアドレス、フルネーム）

        複数のフィールドを対象とした部分一致検索を行います。
        OR条件により、いずれかのフィールドにマッチするユーザーを取得します。

        検索対象フィールド：
        - name: Backlogのユーザー名
        - full_name: フルネーム
        - email: メールアドレス

        検索方式：
        - 部分一致検索（LIKE %query%）
        - 大文字小文字を区別しない（ilike）
        - OR条件で複数フィールドを検索

        Args:
            query (str): 検索クエリ文字列
            skip (int, optional): スキップするレコード数。デフォルトは0
            limit (int, optional): 取得する最大レコード数。デフォルトは100

        Returns:
            List[User]: 検索条件に一致するユーザーのリスト

        Example:
            >>> # "田中"を含むユーザーを検索
            >>> users = user_repo.search(query="田中", limit=10)
            >>> for user in users:
            ...     print(f"Found: {user.name} ({user.email})")

            >>> # メールアドレスで検索
            >>> users = user_repo.search(query="@example.com")

        Note:
            - LIKE検索のため、インデックスが効かない場合がある
            - 大量データの場合は全文検索エンジンの使用を検討
            - 空文字列で検索すると全ユーザーが返る
        """
        # 部分一致検索用のパターン
        search_pattern = f"%{query}%"

        return (
            self.db.query(User)
            .filter(
                or_(User.name.ilike(search_pattern), User.full_name.ilike(search_pattern), User.email.ilike(search_pattern))
            )
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_admins(self) -> List[User]:
        """
        管理者ユーザーを取得

        is_superuser=Trueまたはグローバルな"ADMIN"ロールを持つユーザーを取得します。

        取得条件：
        - is_superuser=True のユーザー、または
        - グローバルなADMINロールを持つユーザー（project_id=NULL）

        Args:
            なし

        Returns:
            List[User]: 管理者ユーザーのリスト

        Example:
            >>> admins = user_repo.get_admins()
            >>> for admin in admins:
            ...     print(f"Admin: {admin.name}")

        Note:
            - ロール情報も効率的に取得（joinedload）
            - 管理者の定義はis_adminプロパティと同じ
        """
        from sqlalchemy import exists

        # is_superuser=True または グローバルなADMINロールを持つユーザーを検索
        return (
            self.db.query(User)
            .options(joinedload(User.user_roles).joinedload(UserRole.role))
            .filter(
                or_(
                    User.is_superuser == True,
                    exists().where(
                        and_(
                            UserRole.user_id == User.id,
                            UserRole.project_id.is_(None),
                            UserRole.role_id == Role.id,
                            Role.name == "ADMIN",
                        )
                    ),
                )
            )
            .all()
        )

    def get_users_by_project(self, project_id: int, skip: int = 0, limit: int = 100) -> List[User]:
        """
        指定されたプロジェクトのメンバーを取得

        多対多のリレーション（project_members中間テーブル）を使用して、
        特定のプロジェクトに所属するユーザーを取得します。

        Args:
            project_id (int): プロジェクトID
            skip (int, optional): スキップするレコード数。デフォルトは0
            limit (int, optional): 取得する最大レコード数。デフォルトは100

        Returns:
            List[User]: プロジェクトメンバーのリスト

        Example:
            >>> members = user_repo.get_users_by_project(project_id=1)
            >>> print(f"Project has {len(members)} members")

        Note:
            - 中間テーブル経由の効率的なJOIN
            - プロジェクト情報は含まれない（必要に応じてjoinedloadを追加）
        """
        from app.models.project import Project

        return self.db.query(User).join(User.projects).filter(Project.id == project_id).offset(skip).limit(limit).all()

    def count_by_project(self, project_id: int) -> int:
        """
        指定されたプロジェクトのメンバー数をカウント

        Args:
            project_id (int): プロジェクトID

        Returns:
            int: プロジェクトメンバー数

        Example:
            >>> member_count = user_repo.count_by_project(project_id=1)
            >>> print(f"Members: {member_count}")

        Note:
            - COUNT(*)による高速カウント
            - 大量データでもパフォーマンス良好
        """
        from app.models.project import Project
        from sqlalchemy import func

        return self.db.query(func.count(User.id)).join(User.projects).filter(Project.id == project_id).scalar() or 0
