"""
ユーザー同期サービス

このモジュールは、Backlogからユーザー情報を同期する機能を提供します。

主な機能:
- Backlogから全プロジェクトのユーザーをインポート
- ユーザー情報の更新
- メールアドレスの更新
- デフォルトロールの自動付与

使用例:
    user_sync_service = UserSyncService()
    result = await user_sync_service.import_users_from_backlog(
        user=current_user,
        access_token=token,
        db=db,
        mode="active_only",
        assign_default_role=True
    )
"""

from typing import Dict, Any, Literal
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.services.backlog_client import backlog_client
from app.services.sync.base_sync_service import BaseSyncService
from app.models.user import User
from app.models.sync_history import SyncType
from app.models.rbac import Role, UserRole
from app.core.permissions import RoleType
import logging

logger = logging.getLogger(__name__)


class UserSyncService(BaseSyncService):
    """
    ユーザー同期サービス

    Backlogからユーザー情報を取得し、Team Insightのデータベースと同期します。
    全プロジェクトのユーザーを収集し、重複を排除してインポートします。

    継承:
        BaseSyncService: 共通機能（同期履歴管理など）を提供
    """

    async def import_users_from_backlog(
        self,
        user: User,
        access_token: str,
        db: Session,
        mode: Literal["all", "active_only"] = "active_only",
        assign_default_role: bool = True,
    ) -> Dict[str, Any]:
        """
        Backlogから全プロジェクトのユーザーをインポート

        全プロジェクトを走査してユーザーを収集し、Team Insightに登録します。
        重複したユーザーは自動的に排除され、各ユーザーは1回のみ処理されます。

        処理フロー:
            1. Backlogから全プロジェクトを取得
            2. 各プロジェクトのユーザーを取得
            3. ユーザーの詳細情報を取得（メールアドレスなど）
            4. 重複を排除してユニークなユーザーリストを作成
            5. 各ユーザーを作成または更新
            6. 新規ユーザーにデフォルトロールを付与（オプション）
            7. 同期結果を返却

        Args:
            user: 実行ユーザー（管理者権限が必要）
            access_token: Backlog APIアクセストークン
            db: データベースセッション
            mode: インポートモード
                - "all": 全ユーザーをインポート
                - "active_only": アクティブなユーザーのみインポート
            assign_default_role: Trueの場合、新規ユーザーにMEMBERロールを自動付与

        Returns:
            インポート結果の辞書
            {
                "success": True,
                "created": 5,  # 新規作成したユーザー数
                "updated": 10,  # 更新したユーザー数
                "skipped": 0,   # スキップしたユーザー数
                "total": 15,    # 処理したユニークユーザー数
                "projects_scanned": 8,  # 走査したプロジェクト数
                "default_role_assigned": True  # デフォルトロールの付与状況
            }

        Raises:
            Exception: Backlog APIエラー、データベースエラーなど

        Note:
            - この処理は時間がかかる可能性があります
            - 同期履歴はSyncType.ALL_USERSとして記録されます
            - 既存ユーザーでもロールを持たない場合、デフォルトロールが付与されます
            - ユーザー詳細情報の取得に失敗しても、基本情報でインポートを続行します

        Example:
            result = await user_sync_service.import_users_from_backlog(
                user=admin_user,
                access_token="abc123...",
                db=db,
                mode="active_only",
                assign_default_role=True
            )
            print(f"新規: {result['created']}名、更新: {result['updated']}名")
        """
        logger.info(
            f"Backlogユーザーインポート開始: " f"user_id={user.id}, mode={mode}, " f"assign_default_role={assign_default_role}"
        )

        # 同期履歴を作成
        sync_history = self._create_sync_history(
            db=db, user_id=user.id, sync_type=SyncType.ALL_USERS, target_name=f"Import Users ({mode})"
        )

        try:
            # 全プロジェクトを取得
            projects_data = await backlog_client.get_projects(access_token)
            logger.info(f"プロジェクトを取得しました: {len(projects_data)}件")

            # ユニークなユーザーを収集（重複排除）
            unique_users = await self._collect_unique_users(projects_data=projects_data, access_token=access_token)
            logger.info(f"ユニークなユーザーを収集しました: {len(unique_users)}名")

            # MEMBERロールを取得（デフォルトロール付与用）
            member_role = None
            if assign_default_role:
                member_role = db.query(Role).filter(Role.name == RoleType.MEMBER).first()
                logger.info(f"デフォルトロール付与: {member_role is not None}")

            # ユーザーをインポート
            created_users, updated_users, skipped_users = await self._import_users(
                unique_users=unique_users,
                mode=mode,
                member_role=member_role,
                assign_default_role=assign_default_role,
                access_token=access_token,
                db=db,
            )

            # 同期履歴を完了としてマーク
            sync_history.complete(items_created=created_users, items_updated=updated_users, total_items=len(unique_users))

            db.commit()

            logger.info(f"ユーザーインポート完了: " f"created={created_users}, updated={updated_users}")

            return {
                "success": True,
                "created": created_users,
                "updated": updated_users,
                "skipped": skipped_users,
                "total": len(unique_users),
                "projects_scanned": len(projects_data),
                "default_role_assigned": assign_default_role and member_role is not None,
            }

        except Exception as e:
            self._handle_sync_error(error=e, sync_history=sync_history, db=db, context="ユーザーインポート")
            raise

    async def _collect_unique_users(self, projects_data: list, access_token: str) -> Dict[int, Dict[str, Any]]:
        """
        全プロジェクトからユニークなユーザーを収集する

        各プロジェクトのユーザーを取得し、backlog_idで重複を排除します。

        Args:
            projects_data: プロジェクトデータのリスト
            access_token: Backlog APIアクセストークン

        Returns:
            backlog_id -> user_dataのマップ

        Note:
            - 同じユーザーが複数のプロジェクトに所属していても、1回のみ処理されます
            - プロジェクトのユーザー取得に失敗した場合は警告ログを出力して続行します
        """
        unique_users = {}  # backlog_id -> user_data

        for project_data in projects_data:
            try:
                # プロジェクトのユーザーを取得
                project_users = await backlog_client.get_project_users(project_data["id"], access_token)

                # ユニークなユーザーを収集
                for user_data in project_users:
                    backlog_id = user_data["id"]
                    if backlog_id not in unique_users:
                        unique_users[backlog_id] = user_data

            except Exception as e:
                logger.warning(f"プロジェクト '{project_data['name']}' のユーザー取得に失敗: " f"{str(e)}")
                continue

        return unique_users

    async def _import_users(
        self,
        unique_users: Dict[int, Dict[str, Any]],
        mode: str,
        member_role: Role,
        assign_default_role: bool,
        access_token: str,
        db: Session,
    ) -> tuple[int, int, int]:
        """
        ユーザーをインポートする

        Args:
            unique_users: backlog_id -> user_dataのマップ
            mode: インポートモード
            member_role: MEMBERロールオブジェクト
            assign_default_role: デフォルトロールを付与するか
            access_token: Backlog APIアクセストークン
            db: データベースセッション

        Returns:
            (created_users, updated_users, skipped_users)のタプル

        Note:
            - ユーザー詳細情報の取得に失敗しても、基本情報でインポートを続行します
            - 既存ユーザーでもロールを持たない場合、デフォルトロールを付与します
        """
        created_users = 0
        updated_users = 0
        skipped_users = 0

        for backlog_id, user_data in unique_users.items():
            # ユーザーの詳細情報を取得（メールアドレスを含む）
            try:
                user_id_str = user_data.get("userId") or str(backlog_id)
                detailed_user_data = await backlog_client.get_user_by_id(user_id_str, access_token)
                # 詳細情報で上書き
                user_data.update(detailed_user_data)
                logger.debug(f"ユーザー詳細情報を取得: {user_data['name']}, " f"email={user_data.get('mailAddress')}")
            except Exception as e:
                logger.warning(f"ユーザー '{user_data['name']}' (ID: {backlog_id}) の詳細情報取得に失敗: " f"{str(e)}")
                # 詳細情報の取得に失敗しても、基本情報でインポートを続行

            # 既存ユーザーを確認
            existing_user = db.query(User).filter(User.backlog_id == backlog_id).first()

            if existing_user:
                # 既存ユーザーを更新
                updated_users += self._update_existing_user(
                    existing_user=existing_user,
                    user_data=user_data,
                    mode=mode,
                    member_role=member_role,
                    assign_default_role=assign_default_role,
                    db=db,
                )
            else:
                # 新規ユーザーを作成
                created_users += self._create_new_user(
                    backlog_id=backlog_id,
                    user_data=user_data,
                    member_role=member_role,
                    assign_default_role=assign_default_role,
                    db=db,
                )

        return created_users, updated_users, skipped_users

    def _update_existing_user(
        self,
        existing_user: User,
        user_data: Dict[str, Any],
        mode: str,
        member_role: Role,
        assign_default_role: bool,
        db: Session,
    ) -> int:
        """
        既存ユーザーを更新する

        Args:
            existing_user: 既存のユーザーオブジェクト
            user_data: Backlogから取得したユーザーデータ
            mode: インポートモード
            member_role: MEMBERロールオブジェクト
            assign_default_role: デフォルトロールを付与するか
            db: データベースセッション

        Returns:
            更新した場合は1、しなかった場合は0

        Note:
            - 名前とメールアドレスを更新します
            - active_onlyモードの場合、is_activeをTrueに設定します
            - ロールを持たない場合、デフォルトロールを付与します
        """
        # 既存ユーザーの情報を更新
        existing_user.name = user_data["name"]
        if user_data.get("mailAddress"):
            existing_user.email = user_data.get("mailAddress")

        # active_onlyモードの場合、is_activeをTrueに設定
        if mode == "active_only":
            existing_user.is_active = True

        # 既存ユーザーでもロールを持っていない場合はデフォルトロールを付与
        if member_role and assign_default_role:
            # ユーザーがグローバルロールを持っているか確認
            has_global_role = (
                db.query(UserRole).filter(UserRole.user_id == existing_user.id, UserRole.project_id.is_(None)).first()
            )

            if not has_global_role:
                user_role = UserRole(user_id=existing_user.id, role_id=member_role.id, project_id=None)  # グローバルロール
                db.add(user_role)
                logger.info(f"ユーザー '{existing_user.name}' (ID: {existing_user.id}) に" f"MEMBERロールを付与しました")

        return 1

    def _create_new_user(
        self, backlog_id: int, user_data: Dict[str, Any], member_role: Role, assign_default_role: bool, db: Session
    ) -> int:
        """
        新規ユーザーを作成する

        Args:
            backlog_id: BacklogユーザーID
            user_data: Backlogから取得したユーザーデータ
            member_role: MEMBERロールオブジェクト
            assign_default_role: デフォルトロールを付与するか
            db: データベースセッション

        Returns:
            作成した場合は1、しなかった場合は0

        Note:
            - デフォルトでis_active=Trueで作成されます
            - assign_default_roleがTrueの場合、MEMBERロールを付与します
        """
        # 新規ユーザーを作成
        new_user = User(
            backlog_id=backlog_id,
            user_id=user_data.get("userId"),
            name=user_data["name"],
            email=user_data.get("mailAddress"),
            is_active=True,
        )
        db.add(new_user)
        db.flush()  # IDを取得

        # デフォルトロールを付与
        if member_role and assign_default_role:
            user_role = UserRole(user_id=new_user.id, role_id=member_role.id, project_id=None)  # グローバルロール
            db.add(user_role)
            logger.info(f"新規ユーザー '{new_user.name}' (ID: {new_user.id}) を作成し、" f"MEMBERロールを付与しました")
        else:
            logger.info(f"新規ユーザー '{new_user.name}' (ID: {new_user.id}) を作成しました")

        return 1

    async def update_users_email_addresses(self, user: User, access_token: str, db: Session) -> Dict[str, Any]:
        """
        既存ユーザーのメールアドレスを更新

        メールアドレスが未設定のユーザーに対して、
        Backlog APIから詳細情報を取得してメールアドレスを更新します。

        処理フロー:
            1. メールアドレスが未設定のユーザーを取得
            2. 各ユーザーの詳細情報をBacklog APIから取得
            3. メールアドレスを更新
            4. 更新結果を返却

        Args:
            user: 実行ユーザー
            access_token: Backlog APIアクセストークン
            db: データベースセッション

        Returns:
            更新結果の辞書
            {
                "success": True,
                "updated": 5,  # 更新したユーザー数
                "failed": 1,   # 失敗したユーザー数
                "total_without_email": 6  # メールアドレス未設定のユーザー総数
            }

        Note:
            - backlog_idとuser_idが設定されているユーザーのみ処理されます
            - 個別のユーザー更新に失敗しても、処理は続行されます
            - 失敗したユーザーは警告ログに記録されます

        Example:
            result = await user_sync_service.update_users_email_addresses(
                user=current_user,
                access_token=token,
                db=db
            )
            print(f"更新: {result['updated']}名、失敗: {result['failed']}名")
        """
        logger.info("メールアドレス未設定ユーザーの更新を開始")

        # メールアドレスが未設定のユーザーを取得
        users_without_email = (
            db.query(User).filter(User.email.is_(None), User.backlog_id.isnot(None), User.user_id.isnot(None)).all()
        )

        logger.info(f"メールアドレス未設定のユーザー: {len(users_without_email)}名")

        updated_count = 0
        failed_count = 0

        for user_record in users_without_email:
            try:
                # ユーザーの詳細情報を取得
                user_id_str = user_record.user_id or str(user_record.backlog_id)
                detailed_user_data = await backlog_client.get_user_by_id(user_id_str, access_token)

                # メールアドレスを更新
                if detailed_user_data.get("mailAddress"):
                    user_record.email = detailed_user_data["mailAddress"]
                    updated_count += 1
                    logger.info(f"ユーザー '{user_record.name}' のメールアドレスを更新: " f"{user_record.email}")
                else:
                    logger.debug(f"ユーザー '{user_record.name}' のメールアドレスが見つかりません")

            except Exception as e:
                logger.warning(f"ユーザー '{user_record.name}' のメールアドレス更新に失敗: " f"{str(e)}")
                failed_count += 1
                continue

        db.commit()

        logger.info(f"メールアドレス更新完了: " f"updated={updated_count}, failed={failed_count}")

        return {
            "success": True,
            "updated": updated_count,
            "failed": failed_count,
            "total_without_email": len(users_without_email),
        }


# シングルトンインスタンス
user_sync_service = UserSyncService()
