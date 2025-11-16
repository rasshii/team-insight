"""
プロジェクト同期サービス

このモジュールは、Backlogからプロジェクト情報を同期する機能を提供します。

主な機能:
- 全プロジェクトの同期
- 個別プロジェクトの同期
- プロジェクトメンバーの同期
- 同期後のキャッシュ無効化

使用例:
    project_sync_service = ProjectSyncService()
    result = await project_sync_service.sync_all_projects(
        user=current_user,
        access_token=token,
        db=db
    )
"""

from typing import Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.services.backlog_client import backlog_client
from app.services.sync.base_sync_service import BaseSyncService
from app.models.user import User
from app.models.project import Project
from app.models.sync_history import SyncHistory, SyncType, SyncStatus
from app.core.exceptions import ExternalAPIException
import logging

logger = logging.getLogger(__name__)


class ProjectSyncService(BaseSyncService):
    """
    プロジェクト同期サービス

    Backlogからプロジェクト情報を取得し、Team Insightのデータベースと同期します。
    プロジェクトの基本情報とメンバー情報を同期し、キャッシュを自動的に無効化します。

    継承:
        BaseSyncService: 共通機能（同期履歴管理など）を提供
    """

    async def sync_all_projects(self, user: User, access_token: str, db: Session) -> Dict[str, Any]:
        """
        全プロジェクトを同期

        Backlogから全プロジェクトの一覧を取得し、各プロジェクトの基本情報と
        メンバー情報を同期します。同期完了後、プロジェクト関連のキャッシュを
        自動的に無効化します。

        処理フロー:
            1. 同期履歴を作成（SyncType.ALL_PROJECTS）
            2. Backlogから全プロジェクトを取得
            3. 各プロジェクトを同期（基本情報 + メンバー）
            4. 同期履歴を完了としてマーク
            5. プロジェクト関連のキャッシュを無効化
            6. 同期結果を返却

        Args:
            user: 実行ユーザー（管理者またはプロジェクトリーダー権限が必要）
            access_token: Backlog APIアクセストークン
            db: データベースセッション

        Returns:
            同期結果の辞書
            {
                "success": True,
                "created": 3,  # 新規作成したプロジェクト数
                "updated": 7,  # 更新したプロジェクト数
                "total": 10    # 処理したプロジェクト総数
            }

        Raises:
            Exception: Backlog APIエラー、データベースエラーなど

        Note:
            - この処理は時間がかかる可能性があります（プロジェクト数に依存）
            - 各プロジェクトのメンバー情報も自動的に同期されます
            - 同期完了後、プロジェクト関連のキャッシュが自動的に無効化されます
            - 同期履歴はsync_historyテーブルに記録されます

        Example:
            result = await project_sync_service.sync_all_projects(
                user=current_user,
                access_token="abc123...",
                db=db
            )
            print(f"新規: {result['created']}件、更新: {result['updated']}件")
        """
        logger.info(f"全プロジェクト同期開始: user_id={user.id}")

        # 同期履歴を作成
        sync_history = SyncHistory(
            user_id=user.id, sync_type=SyncType.ALL_PROJECTS, status=SyncStatus.STARTED, target_name="All Projects"
        )
        db.add(sync_history)
        db.flush()

        try:
            # Backlogから全プロジェクトを取得
            logger.info(f"Backlogからプロジェクトを取得中...")
            projects_data = await backlog_client.get_projects(access_token)
            logger.info(f"プロジェクトを取得しました: {len(projects_data)}件")

            created_count = 0
            updated_count = 0

            # 各プロジェクトを同期
            for project_data in projects_data:
                logger.debug(f"プロジェクトを同期中: " f"{project_data.get('projectKey')} - {project_data.get('name')}")

                # プロジェクト基本情報を同期
                project = await self._sync_project(project_data, db)

                if project.created_at == project.updated_at:
                    created_count += 1
                else:
                    updated_count += 1

                # プロジェクトメンバーを同期
                await self._sync_project_members(project=project, project_data=project_data, access_token=access_token, db=db)

            # 同期履歴を完了としてマーク
            sync_history.complete(items_created=created_count, items_updated=updated_count, total_items=len(projects_data))

            db.commit()

            # キャッシュを無効化
            await self._invalidate_cache(pattern="cache:http:*projects*", context="プロジェクト同期")

            logger.info(
                f"全プロジェクト同期完了: "
                f"user_id={user.id}, created={created_count}, "
                f"updated={updated_count}, total={len(projects_data)}"
            )

            return {"success": True, "created": created_count, "updated": updated_count, "total": len(projects_data)}

        except Exception as e:
            self._handle_sync_error(error=e, sync_history=sync_history, db=db, context="全プロジェクト同期")
            raise

    async def sync_single_project(self, project_id: int, access_token: str, db: Session) -> Project:
        """
        単一のプロジェクトを同期

        指定されたプロジェクトの情報をBacklogから取得し、同期します。

        Args:
            project_id: BacklogプロジェクトID
            access_token: Backlog APIアクセストークン
            db: データベースセッション

        Returns:
            同期されたプロジェクトオブジェクト

        Raises:
            Exception: Backlog APIエラー、データベースエラーなど

        Note:
            - この処理では同期履歴は作成されません
            - メンバー情報は同期されません（基本情報のみ）

        Example:
            project = await project_sync_service.sync_single_project(
                project_id=12345,
                access_token="abc123...",
                db=db
            )
        """
        try:
            # Backlogからプロジェクト情報を取得
            project_data = await backlog_client.get_project_by_id(project_id, access_token)

            # プロジェクトを同期
            project = await self._sync_project(project_data, db)

            db.commit()

            logger.info(f"単一プロジェクト同期完了: " f"project_id={project.id}, backlog_id={project.backlog_id}")

            return project

        except Exception as e:
            logger.error(f"単一プロジェクト同期失敗: " f"project_id={project_id}, error={str(e)}", exc_info=True)
            db.rollback()
            raise

    async def _sync_project(self, project_data: Dict[str, Any], db: Session) -> Project:
        """
        プロジェクトデータを同期（内部メソッド）

        Backlogから取得したプロジェクトデータを元に、
        既存のプロジェクトを更新するか、新規作成します。

        Args:
            project_data: Backlog APIから取得したプロジェクトデータ
            db: データベースセッション

        Returns:
            同期されたプロジェクトオブジェクト

        Note:
            - backlog_idで既存プロジェクトを検索します
            - 存在しない場合は新規作成します
            - db.flush()を呼び出してIDを取得します（commit()は呼び出しません）

        処理内容:
            - プロジェクト名
            - プロジェクトキー
            - プロジェクト説明
            - プロジェクトステータス（アーカイブ済みかどうか）
        """
        # 既存のプロジェクトを検索
        project = db.query(Project).filter(Project.backlog_id == project_data["id"]).first()

        if not project:
            # 新規プロジェクトを作成
            project = Project(backlog_id=project_data["id"])
            db.add(project)
            logger.info(f"新規プロジェクトを作成: " f"backlog_id={project_data['id']}, " f"key={project_data['projectKey']}")
        else:
            logger.debug(
                f"既存プロジェクトを更新: "
                f"id={project.id}, backlog_id={project.backlog_id}, "
                f"key={project_data['projectKey']}"
            )

        # プロジェクト情報を更新
        project.name = project_data["name"]
        project.project_key = project_data["projectKey"]
        project.description = project_data.get("description", "")
        project.status = "active" if not project_data.get("archived") else "archived"

        db.flush()  # IDを取得するため
        return project

    async def _sync_project_members(
        self, project: Project, project_data: Dict[str, Any], access_token: str, db: Session
    ) -> None:
        """
        プロジェクトメンバーを同期

        指定されたプロジェクトのメンバー情報をBacklogから取得し、同期します。
        メンバーとして登録されているユーザーが存在しない場合は自動的に作成されます。

        処理フロー:
            1. Backlogからプロジェクトメンバーを取得
            2. 各メンバーの詳細情報を取得（メールアドレスなど）
            3. ユーザーが存在しない場合は作成
            4. プロジェクトのmembersリレーションを更新

        Args:
            project: プロジェクトオブジェクト
            project_data: Backlog APIから取得したプロジェクトデータ
            access_token: Backlog APIアクセストークン
            db: データベースセッション

        Note:
            - メンバー同期の失敗はプロジェクト同期全体を止めません
            - ユーザー詳細情報の取得に失敗しても、基本情報でメンバーを作成します
            - 重複エラーが発生した場合は、既存ユーザーを取得します

        Raises:
            ExternalAPIException: Backlog APIエラー（上位で処理される）

        Example:
            await self._sync_project_members(
                project=project,
                project_data=project_data,
                access_token=token,
                db=db
            )
        """
        try:
            # Backlogからプロジェクトメンバーを取得
            members_data = await backlog_client.get_project_users(project.backlog_id, access_token)

            # プロジェクトメンバーとして設定するユーザーリスト
            all_users = []

            for member_data in members_data:
                # ユーザーの詳細情報を取得（メールアドレスを含む）
                try:
                    user_id_str = member_data.get("userId") or str(member_data["id"])
                    detailed_member_data = await backlog_client.get_user_by_id(user_id_str, access_token)
                    # 詳細情報で上書き
                    member_data.update(detailed_member_data)
                except Exception as e:
                    logger.debug(f"メンバー '{member_data.get('name', 'Unknown')}' の詳細情報取得に失敗: " f"{str(e)}")

                # 既存ユーザーを検索
                user = db.query(User).filter(User.backlog_id == member_data["id"]).first()

                if not user:
                    # 新規ユーザーを作成
                    user = User(
                        backlog_id=member_data["id"],
                        user_id=member_data.get("userId"),
                        name=member_data["name"],
                        email=member_data.get("mailAddress"),
                        is_active=True,
                    )
                    db.add(user)

                    # 個別にflushして重複エラーを回避
                    try:
                        db.flush()
                        logger.info(
                            f"プロジェクトメンバーとして新規ユーザーを作成: "
                            f"backlog_id={member_data['id']}, name={member_data['name']}"
                        )
                    except SQLAlchemyError as e:
                        # 重複エラーの場合は既存ユーザーを取得
                        db.rollback()
                        user = db.query(User).filter(User.backlog_id == member_data["id"]).first()
                        if not user:
                            logger.error(f"ユーザーの作成・取得に失敗: " f"backlog_id={member_data['id']}")
                            continue
                else:
                    # 既存ユーザーの情報を更新
                    user.name = member_data["name"]
                    if member_data.get("mailAddress"):
                        user.email = member_data.get("mailAddress")
                    user.is_active = True

                all_users.append(user)

            # プロジェクトメンバーを更新
            project.members = all_users

            logger.info(f"プロジェクト '{project.project_key}' のメンバーを同期: " f"{len(all_users)}名")
            logger.debug(f"プロジェクト '{project.project_key}' メンバーID: " f"{[u.id for u in all_users]}")
            logger.debug(f"プロジェクト '{project.project_key}' メンバー名: " f"{[u.name for u in all_users]}")

        except ExternalAPIException:
            # Backlog APIエラーは再raise（上位で適切に処理される）
            raise
        except SQLAlchemyError as e:
            logger.error(f"プロジェクトメンバー同期中のデータベースエラー: {str(e)}")
            # メンバー同期の失敗はプロジェクト同期全体を止めない
        except Exception as e:
            logger.error(f"プロジェクトメンバー同期中の予期しないエラー: {str(e)}", exc_info=True)
            # メンバー同期の失敗はプロジェクト同期全体を止めない


# シングルトンインスタンス
project_sync_service = ProjectSyncService()
