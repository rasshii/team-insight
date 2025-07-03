"""
Backlog認証のバリデーション機能

このモジュールは、Backlog OAuthで認証されたユーザーの
アクセス権限を検証する機能を提供します。
"""
from typing import Optional, List
import logging
from app.core.config import settings
from app.core.exceptions import ValidationException

logger = logging.getLogger(__name__)


class BacklogAuthValidator:
    """Backlog認証のバリデーションクラス"""
    
    @staticmethod
    def validate_space_access(space_key: str) -> None:
        """
        スペースへのアクセス権限を検証
        
        Args:
            space_key: Backlogスペースキー
            
        Raises:
            ValidationException: アクセスが許可されていない場合
        """
        # 環境変数から許可されたスペースを取得
        allowed_spaces_str = getattr(settings, 'ALLOWED_BACKLOG_SPACES', '')
        if not allowed_spaces_str:
            # 制限が設定されていない場合は全て許可
            return
            
        allowed_spaces = [s.strip() for s in allowed_spaces_str.split(',') if s.strip()]
        
        if space_key not in allowed_spaces:
            logger.warning(
                f"許可されていないスペースからのアクセス試行: {space_key} "
                f"(許可されたスペース: {', '.join(allowed_spaces)})"
            )
            raise ValidationException(
                field="space",
                detail=(
                    f"申し訳ございません。このアプリケーションは "
                    f"特定のBacklogスペースのメンバーのみ利用可能です。"
                )
            )
    
    @staticmethod
    def validate_email_domain(email: str, allowed_domains: Optional[List[str]] = None) -> None:
        """
        メールドメインを検証
        
        Args:
            email: ユーザーのメールアドレス
            allowed_domains: 許可されたドメインのリスト
            
        Raises:
            ValidationException: ドメインが許可されていない場合
        """
        if not allowed_domains or not email:
            return
            
        if not any(email.endswith(domain) for domain in allowed_domains):
            logger.warning(f"許可されていないメールドメイン: {email}")
            raise ValidationException(
                field="email",
                detail=(
                    "組織外のメールアドレスではこのアプリケーションを"
                    "利用できません。"
                )
            )
    
    @staticmethod
    def validate_user_status(user_info: dict, space_key: str) -> None:
        """
        ユーザーのステータスを検証
        
        Args:
            user_info: Backlogユーザー情報
            space_key: Backlogスペースキー
            
        Raises:
            ValidationException: ユーザーが無効な場合
        """
        # ユーザーが無効化されているかチェック
        # Backlog APIのレスポンスに応じて実装
        # 例: if user_info.get("status") == "inactive":
        #     raise ValidationException(...)
        pass