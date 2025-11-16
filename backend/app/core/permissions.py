# backend/app/core/permissions.py
"""
権限管理とRBAC（Role-Based Access Control）システム

このモジュールは、Team Insightアプリケーションの権限管理機能を提供します。
RBAC（ロールベースアクセス制御）を実装し、ユーザーの役割に基づいて
アクセス制御を行います。

主要な機能:
    1. ロール定義
       - ADMIN: システム管理者（全権限）
       - PROJECT_LEADER: プロジェクトリーダー（プロジェクト管理権限）
       - MEMBER: 一般メンバー（基本権限）

    2. 権限チェック
       - ユーザーのロール確認
       - プロジェクトアクセス権限の確認
       - プロジェクト内での特定権限の確認

    3. デコレータによるアクセス制御
       - @require_role でエンドポイントレベルでの権限制御

主要なクラス・関数:
    - RoleType: ロールの列挙型
    - PermissionChecker: 権限チェッククラス
    - require_role(): ロール必須デコレータ

RBAC設計のポイント:
    - 階層的な権限（ADMINは全ての権限を持つ）
    - プロジェクト単位の権限管理
    - グローバルロールとプロジェクトロールの分離

使用例:
    ```python
    from app.core.permissions import require_role, RoleType, PermissionChecker

    # エンドポイントでのロール制限
    @router.delete("/projects/{project_id}")
    @require_role([RoleType.ADMIN, RoleType.PROJECT_LEADER])
    async def delete_project(
        project_id: int,
        current_user: User = Depends(get_current_active_user)
    ):
        # ADMINまたはPROJECT_LEADERのみアクセス可能
        pass

    # プログラムでの権限チェック
    if PermissionChecker.has_role(user, RoleType.PROJECT_LEADER, project_id):
        # プロジェクトリーダーとして操作を実行
        pass
    ```

セキュリティの考慮事項:
    - 最小権限の原則（必要最小限の権限のみを付与）
    - 明示的な権限チェック（デフォルトは拒否）
    - 階層的な権限（上位ロールは下位ロールの権限を含む）
"""

from enum import Enum
from typing import List, Optional
from functools import wraps
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.models.user import User
from app.models.rbac import UserRole, Role
from app.models.project import Project


class RoleType(str, Enum):
    """
    ユーザーロールの列挙型

    Team Insightシステムで使用される全てのロールを定義します。
    str型を継承しているため、文字列としても使用できます。

    ロールの種類:
        ADMIN: システム管理者
            - 全ての操作が可能
            - 全プロジェクトへのアクセス権限
            - ユーザー管理、システム設定の変更が可能

        PROJECT_LEADER: プロジェクトリーダー
            - プロジェクトの管理権限
            - プロジェクトメンバーの追加/削除
            - プロジェクト設定の変更

        MEMBER: 一般メンバー
            - プロジェクトへの参加権限
            - タスクの作成/更新
            - コメントの投稿

    使用例:
        >>> role = RoleType.ADMIN
        >>> print(role.value)  # "ADMIN"
        >>> if role == RoleType.ADMIN:
        ...     print("管理者です")
    """

    ADMIN = "ADMIN"
    PROJECT_LEADER = "PROJECT_LEADER"
    MEMBER = "MEMBER"


class PermissionChecker:
    """
    権限チェックを行うクラス

    RBACシステムの中核となるクラスで、ユーザーの権限を検証します。
    静的メソッドのみで構成され、インスタンス化せずに使用できます。

    設計の特徴:
        1. 階層的な権限
           - ADMINは全ての権限を持つ
           - 上位ロールは下位ロールの権限を含む可能性

        2. プロジェクト単位の権限管理
           - グローバルロール（全プロジェクトに適用）
           - プロジェクトロール（特定プロジェクトのみ）

        3. 明示的な権限チェック
           - デフォルトは権限なし
           - 明示的に権限があることを確認

    主要なメソッド:
        - has_role(): ユーザーが指定ロールを持つか確認
        - check_project_access(): プロジェクトアクセス権を確認
        - check_project_permission(): プロジェクト内の特定権限を確認

    使用例:
        ```python
        # グローバルロールチェック
        if PermissionChecker.has_role(user, RoleType.ADMIN):
            # 管理者のみの処理
            pass

        # プロジェクト単位のロールチェック
        if PermissionChecker.has_role(user, RoleType.PROJECT_LEADER, project_id=1):
            # プロジェクト1のリーダーとしての処理
            pass

        # プロジェクトアクセス権チェック
        if PermissionChecker.check_project_access(user, project_id=1, db=db):
            # プロジェクト1にアクセス可能
            pass
        ```
    """

    @staticmethod
    def has_role(user: User, role: RoleType, project_id: Optional[int] = None) -> bool:
        """
        ユーザーが指定されたロールを持っているかチェックします

        グローバルロール（全プロジェクトに適用）とプロジェクトロール
        （特定プロジェクトのみ）の両方をサポートします。

        チェックロジック:
            1. 管理者（is_admin=True）の場合、常にTrueを返す
            2. project_idが指定されている場合、そのプロジェクトのロールをチェック
            3. project_idがない場合、グローバルロールをチェック

        Args:
            user (User): チェック対象のユーザー
            role (RoleType): 必要なロール（ADMIN, PROJECT_LEADER, MEMBER）
            project_id (Optional[int], optional): プロジェクトID。
                                                 指定された場合、そのプロジェクト内でのロールをチェック。
                                                 指定されない場合、グローバルロールをチェック。

        Returns:
            bool: ユーザーが指定されたロールを持つ場合True、それ以外はFalse

        Examples:
            >>> # 管理者チェック
            >>> if PermissionChecker.has_role(user, RoleType.ADMIN):
            ...     print("管理者です")

            >>> # プロジェクトリーダーチェック
            >>> project_id = 1
            >>> if PermissionChecker.has_role(user, RoleType.PROJECT_LEADER, project_id):
            ...     print("このプロジェクトのリーダーです")

        Note:
            - is_admin=Trueのユーザーは常にTrueを返します（スーパーユーザー）
            - ユーザーは複数のロールを持つことができます
            - プロジェクトロールとグローバルロールは別々に管理されます
        """
        # 管理者は全権限を持つ（最優先）
        if user.is_admin:
            return True

        # ユーザーが持つ全てのロールを取得
        user_roles = user.roles

        # プロジェクト指定がある場合、そのプロジェクト内でのロールをチェック
        if project_id:
            # 指定されたプロジェクトのロールのみを抽出
            project_roles = [r for r in user_roles if r.project_id == project_id]
            # 指定されたロールを持っているか確認
            return any(r.role.name == role.value for r in project_roles)

        # グローバルロールのチェック（全プロジェクトに適用されるロール）
        # project_id が None のロールを抽出
        global_roles = [r for r in user_roles if r.project_id is None]
        # 指定されたロールを持っているか確認
        return any(r.role.name == role.value for r in global_roles)

    @staticmethod
    def check_project_access(user: User, project_id: int, db: Session) -> bool:
        """
        プロジェクトへのアクセス権限をチェックします

        ユーザーが指定されたプロジェクトのメンバーであるかを確認します。
        管理者は全プロジェクトにアクセス可能です。

        チェックロジック:
            1. 管理者の場合、常にTrue
            2. プロジェクトが存在するか確認
            3. ユーザーがプロジェクトメンバーに含まれているか確認

        Args:
            user (User): チェック対象のユーザー
            project_id (int): プロジェクトID
            db (Session): データベースセッション

        Returns:
            bool: アクセス権限がある場合True、それ以外はFalse

        Examples:
            >>> if PermissionChecker.check_project_access(user, project_id=1, db=db):
            ...     # プロジェクトにアクセス可能
            ...     project_data = get_project_data(project_id)

        Note:
            - プロジェクトが存在しない場合はFalseを返します
            - この関数はN+1問題を避けるため、呼び出し元でeager loadingを推奨
            - 管理者（is_admin=True）は全プロジェクトにアクセス可能
        """
        # 管理者は全プロジェクトにアクセス可能
        if user.is_admin:
            return True

        # プロジェクトをデータベースから取得
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            # プロジェクトが存在しない場合はアクセス不可
            return False

        # ユーザーがプロジェクトメンバーに含まれているかチェック
        # project.membersはリレーションシップで定義されたメンバーリスト
        return user in project.members

    @staticmethod
    def check_project_permission(user: User, project_id: int, required_role: RoleType, db: Session) -> bool:
        """
        プロジェクト内での特定の権限をチェックします

        プロジェクトへのアクセス権限と、そのプロジェクト内での
        特定のロールの両方をチェックします。

        チェックロジック:
            1. 管理者の場合、常にTrue
            2. プロジェクトアクセス権限を確認
            3. プロジェクト内での指定されたロールを持つか確認

        Args:
            user (User): チェック対象のユーザー
            project_id (int): プロジェクトID
            required_role (RoleType): 必要なロール
            db (Session): データベースセッション

        Returns:
            bool: 権限がある場合True、それ以外はFalse

        Examples:
            >>> # プロジェクト削除権限のチェック
            >>> can_delete = PermissionChecker.check_project_permission(
            ...     user, project_id=1, required_role=RoleType.PROJECT_LEADER, db=db
            ... )
            >>> if can_delete:
            ...     delete_project(project_id)

        Note:
            - プロジェクトメンバーでない場合、必ずFalseを返します
            - 管理者は全ての権限チェックでTrueを返します
            - この関数は check_project_access() と has_role() を組み合わせたものです
        """
        # 管理者は全権限を持つ
        if user.is_admin:
            return True

        # プロジェクトへのアクセス権限を確認
        # メンバーでない場合は、ロールに関わらずアクセス不可
        if not PermissionChecker.check_project_access(user, project_id, db):
            return False

        # プロジェクト内での役割を確認
        # メンバーであることが確認された上で、指定されたロールを持つかチェック
        return PermissionChecker.has_role(user, required_role, project_id)


def require_role(roles: List[RoleType]):
    """
    ロールベースのアクセス制御デコレータ

    エンドポイント関数にデコレートすることで、指定されたロールを持つ
    ユーザーのみがアクセスできるように制限します。

    デコレータの動作:
        1. current_userをkwargsから取得
        2. ユーザーが認証されているか確認（401エラー）
        3. 指定されたロールのいずれかを持つか確認（403エラー）
        4. 権限があれば元の関数を実行

    Args:
        roles (List[RoleType]): 許可するロールのリスト。
                               いずれか1つを持っていればアクセス可能（OR条件）。

    Returns:
        function: デコレートされた関数

    Raises:
        HTTPException (401 Unauthorized): ユーザーが認証されていない場合
        HTTPException (403 Forbidden): 必要なロールを持っていない場合

    Examples:
        >>> # 管理者のみアクセス可能なエンドポイント
        >>> @router.get("/admin/users")
        >>> @require_role([RoleType.ADMIN])
        >>> async def get_all_users(
        ...     current_user: User = Depends(get_current_active_user)
        ... ):
        ...     # 管理者のみ実行可能
        ...     return db.query(User).all()

        >>> # 管理者またはプロジェクトリーダーがアクセス可能
        >>> @router.delete("/projects/{project_id}")
        >>> @require_role([RoleType.ADMIN, RoleType.PROJECT_LEADER])
        >>> async def delete_project(
        ...     project_id: int,
        ...     current_user: User = Depends(get_current_active_user)
        ... ):
        ...     # いずれかのロールを持つユーザーが実行可能
        ...     delete_project(project_id)

    Note:
        - エンドポイント関数の引数にcurrent_userが必要です
        - Depends(get_current_active_user)と併用してください
        - 複数のロールを指定した場合、OR条件で評価されます
        - プロジェクト固有の権限チェックには適していません
          （プロジェクト単位の権限は別途チェックが必要）

    セキュリティ:
        - 認証が必須（current_userがNoneの場合は401エラー）
        - 明示的にロールをチェック（デフォルトは拒否）
        - 権限不足の場合は403エラー（401ではない）
    """

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 現在のユーザーを関数の引数から取得
            # FastAPIの依存性注入により、current_userがkwargsに含まれる
            current_user = kwargs.get("current_user")

            # ユーザーが認証されているか確認
            if not current_user:
                # current_userがNoneの場合、認証されていない
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="認証が必要です")

            # 権限チェック: 指定されたロールのいずれかを持つか確認
            has_permission = False
            for role in roles:
                # いずれかのロールを持っていればOK（OR条件）
                if PermissionChecker.has_role(current_user, role):
                    has_permission = True
                    break

            # 権限がない場合はエラー
            if not has_permission:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="この操作を実行する権限がありません")

            # 権限チェックを通過したので、元の関数を実行
            return await func(*args, **kwargs)

        return wrapper

    return decorator
