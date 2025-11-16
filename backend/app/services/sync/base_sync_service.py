"""
ベース同期サービス

このモジュールは、全ての同期サービスの基底クラスを提供します。
共通の機能（ユーザー作成、日付パース、同期履歴管理など）を実装し、
各サービスでコードの重複を避けます。

主な機能:
- 同期履歴の作成・更新
- ユーザーの取得または作成
- 日付文字列のパース
- 共通エラーハンドリング

設計原則:
- DRY原則: 共通コードを1箇所にまとめる
- 単一責任原則: 同期に関する共通機能のみを扱う
- 依存性注入: データベースセッションなどを外部から注入
"""

from typing import Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.models.user import User
from app.models.sync_history import SyncHistory, SyncType, SyncStatus
import logging

logger = logging.getLogger(__name__)


class BaseSyncService:
    """
    同期サービスの基底クラス

    全ての同期サービスが継承する基底クラスです。
    共通機能を提供することで、コードの重複を避け、
    保守性を向上させます。

    使用方法:
        class UserSyncService(BaseSyncService):
            async def sync_users(self, ...):
                # 基底クラスのメソッドを利用
                sync_history = self._create_sync_history(...)
                user = self._get_or_create_user(...)
    """

    def _create_sync_history(
        self, db: Session, user_id: int, sync_type: SyncType, target_id: Optional[int] = None, target_name: str = ""
    ) -> SyncHistory:
        """
        同期履歴を作成する

        同期処理の開始時に履歴レコードを作成します。
        同期の追跡とデバッグに使用されます。

        Args:
            db: データベースセッション
            user_id: 同期を実行するユーザーのID
            sync_type: 同期の種類（ユーザー、プロジェクト、タスクなど）
            target_id: 同期対象のID（プロジェクトIDなど）。Noneの場合は全体同期
            target_name: 同期対象の名称（プロジェクト名など）

        Returns:
            作成された同期履歴オブジェクト（ステータス=STARTED）

        Note:
            - 作成後、db.flush()を呼び出してIDを取得します
            - 返されたオブジェクトは、同期完了時にcomplete()またはfail()を呼び出す必要があります

        Example:
            sync_history = self._create_sync_history(
                db=db,
                user_id=user.id,
                sync_type=SyncType.ALL_PROJECTS,
                target_name="All Projects"
            )
            try:
                # 同期処理...
                sync_history.complete(items_created=5, items_updated=10, total_items=15)
            except Exception as e:
                sync_history.fail(str(e))
        """
        sync_history = SyncHistory(
            user_id=user_id, sync_type=sync_type, status=SyncStatus.STARTED, target_id=target_id, target_name=target_name
        )
        db.add(sync_history)
        db.flush()  # IDを取得するため

        logger.info(
            f"同期履歴を作成しました: "
            f"type={sync_type.value}, user_id={user_id}, "
            f"target_id={target_id}, target_name={target_name}"
        )

        return sync_history

    def _get_or_create_user(self, user_data: Dict[str, Any], db: Session) -> User:
        """
        ユーザーを取得または作成する

        Backlog APIから取得したユーザーデータを元に、
        既存のユーザーを取得するか、新規作成します。
        タスク同期時の担当者・報告者の設定に使用されます。

        Args:
            user_data: Backlog APIから取得したユーザーデータ
                必須フィールド: id, name
                任意フィールド: userId, mailAddress
            db: データベースセッション

        Returns:
            取得または作成されたユーザーオブジェクト

        Note:
            - 既存ユーザーは更新しません（名前やメールアドレスは変更しない）
            - 新規作成時はis_active=Trueで作成されます
            - db.flush()を呼び出してIDを取得します（commit()は呼び出しません）

        Example:
            assignee = self._get_or_create_user(
                user_data={
                    "id": 12345,
                    "userId": "john_doe",
                    "name": "John Doe",
                    "mailAddress": "john@example.com"
                },
                db=db
            )
            task.assignee_id = assignee.id
        """
        # backlog_idで既存ユーザーを検索
        user = db.query(User).filter(User.backlog_id == user_data["id"]).first()

        if not user:
            # 新規ユーザーを作成
            user = User(
                backlog_id=user_data["id"],
                user_id=user_data.get("userId"),
                name=user_data["name"],
                email=user_data.get("mailAddress"),
                is_active=True,
            )
            db.add(user)
            db.flush()  # IDを取得するため

            logger.info(
                f"新規ユーザーを作成しました: "
                f"backlog_id={user_data['id']}, name={user_data['name']}, "
                f"email={user_data.get('mailAddress')}"
            )
        else:
            logger.debug(f"既存ユーザーを取得しました: " f"id={user.id}, backlog_id={user.backlog_id}, name={user.name}")

        return user

    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """
        日付文字列をdatetimeオブジェクトにパースする

        Backlog APIから返される日付文字列（ISO 8601形式）を
        Pythonのdatetimeオブジェクトに変換します。

        Args:
            date_str: Backlog APIの日付文字列（例: "2023-12-25T10:30:00Z"）

        Returns:
            パースされたdatetimeオブジェクト
            パースに失敗した場合はNone

        Note:
            - Backlogの日付形式: ISO 8601（例: "2023-12-25T10:30:00Z"）
            - Zサフィックスは+00:00に置換されます（UTC）
            - 不正な形式の場合は警告ログを出力してNoneを返します

        Example:
            due_date = self._parse_date("2023-12-25T10:30:00Z")
            if due_date:
                task.due_date = due_date
        """
        if not date_str:
            return None

        try:
            # Backlogの日付形式: "2023-12-25T10:30:00Z"
            # Zサフィックスを+00:00に置換してパース
            return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        except (ValueError, TypeError) as e:
            logger.warning(f"日付のパースに失敗しました: {date_str} - {str(e)}")
            return None

    def _handle_sync_error(
        self, error: Exception, sync_history: Optional[SyncHistory], db: Session, context: str = ""
    ) -> None:
        """
        同期エラーを処理する

        同期中に発生したエラーを記録し、ロールバックを実行します。

        Args:
            error: 発生した例外
            sync_history: 同期履歴オブジェクト（Noneの場合もあり）
            db: データベースセッション
            context: エラーのコンテキスト（ログ出力用）

        Note:
            - エラーをログに記録します
            - sync_historyが存在する場合、fail()を呼び出します
            - データベースをロールバックします
            - 例外は再raiseしません（呼び出し側で処理する必要があります）

        Example:
            try:
                # 同期処理...
            except Exception as e:
                self._handle_sync_error(
                    error=e,
                    sync_history=sync_history,
                    db=db,
                    context="プロジェクト同期"
                )
                raise
        """
        error_message = f"{context}: {str(error)}" if context else str(error)
        logger.error(f"同期エラーが発生しました: {error_message}", exc_info=True)

        # 同期履歴を失敗としてマーク
        if sync_history:
            try:
                sync_history.fail(error_message)
            except Exception as history_error:
                logger.error(f"同期履歴の更新に失敗しました: {str(history_error)}")

        # データベースをロールバック
        try:
            db.rollback()
        except Exception as rollback_error:
            logger.error(f"ロールバックに失敗しました: {str(rollback_error)}")

    async def _invalidate_cache(self, pattern: str, context: str = "") -> None:
        """
        キャッシュを無効化する

        同期完了後にRedisキャッシュを無効化します。
        キャッシュ削除の失敗は同期処理全体を止めません。

        Args:
            pattern: 削除するキャッシュのパターン（例: "cache:http:*projects*"）
            context: ログ出力用のコンテキスト（例: "プロジェクト同期"）

        Note:
            - キャッシュ削除の失敗は警告ログを出力するのみで、例外は発生しません
            - Redis接続エラーなどで失敗しても、同期処理は成功として扱われます

        Example:
            await self._invalidate_cache(
                pattern="cache:http:*projects*",
                context="プロジェクト同期"
            )
        """
        try:
            from app.core.redis_client import redis_client

            deleted_count = await redis_client.delete_pattern(pattern)

            log_message = f"キャッシュを無効化しました: {deleted_count}件削除"
            if context:
                log_message = f"{context} - {log_message}"

            logger.info(log_message)
        except Exception as e:
            warning_message = f"キャッシュの無効化に失敗しました: {str(e)}"
            if context:
                warning_message = f"{context} - {warning_message}"

            logger.warning(warning_message)
            # キャッシュ削除の失敗は同期処理全体を止めない
