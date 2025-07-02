"""
認証関連のビジネスロジック

認証フローの各ステップを管理し、責任を適切に分離します。
"""
from typing import Optional, Tuple
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
import logging
import json
import base64
import secrets

from app.models.user import User
from app.models.auth import OAuthState, OAuthToken
from app.models.rbac import Role, UserRole
from app.core.exceptions import ValidationException, NotFoundException
from app.core.security import create_access_token, create_refresh_token
from app.services.backlog_oauth import BacklogOAuthService
from app.core.utils import QueryBuilder
from app.core.config import settings
from app.services.auth_validator import BacklogAuthValidator

logger = logging.getLogger(__name__)


class AuthService:
    """認証関連のビジネスロジックを管理するサービス"""
    
    def __init__(self, backlog_oauth_service: BacklogOAuthService):
        self.backlog_oauth_service = backlog_oauth_service
    
    def validate_oauth_state(self, db: Session, state: str) -> OAuthState:
        """
        OAuthのstateパラメータを検証
        
        Args:
            db: データベースセッション
            state: 検証するstateパラメータ
            
        Returns:
            有効なOAuthStateオブジェクト
            
        Raises:
            ValidationException: stateが無効または期限切れの場合
        """
        oauth_state = db.query(OAuthState).filter(OAuthState.state == state).first()
        
        if not oauth_state:
            logger.error(f"無効なstateパラメータ - state: {state}")
            # デバッグ用：現在のstateをすべて表示
            all_states = db.query(OAuthState).all()
            logger.debug(f"現在のstate一覧: {[s.state for s in all_states]}")
            raise ValidationException(detail="無効なstateパラメータです")
        
        if oauth_state.is_expired():
            logger.error(f"stateパラメータの有効期限切れ - state: {state}")
            db.delete(oauth_state)
            db.commit()
            raise ValidationException(detail="stateパラメータの有効期限が切れています")
        
        return oauth_state
    
    def extract_space_key_from_state(self, state: str) -> str:
        """
        stateパラメータからspace_keyを抽出
        
        Args:
            state: stateパラメータ
            
        Returns:
            space_key（抽出できない場合はデフォルト値）
        """
        try:
            # Base64デコード
            state_json = base64.urlsafe_b64decode(state.encode()).decode()
            state_data = json.loads(state_json)
            space_key = state_data.get("space_key", settings.BACKLOG_SPACE_KEY)
            logger.info(f"stateからspace_keyを取得 - space_key: {space_key}")
            return space_key
        except Exception as e:
            logger.warning(f"stateのデコードに失敗（旧形式の可能性）: {str(e)}")
            # 旧形式のstateの場合は環境変数のデフォルト値を使用
            return settings.BACKLOG_SPACE_KEY
    
    async def exchange_code_for_token(self, code: str, space_key: str) -> dict:
        """
        認証コードをアクセストークンに交換
        
        Args:
            code: 認証コード
            space_key: Backlogスペースキー
            
        Returns:
            トークン情報
            
        Raises:
            ExternalAPIException: トークン交換に失敗した場合
        """
        logger.info("認証コードをアクセストークンに交換中...")
        return await self.backlog_oauth_service.exchange_code_for_token(code, space_key=space_key)
    
    async def get_backlog_user_info(self, access_token: str, space_key: str) -> dict:
        """
        Backlogからユーザー情報を取得
        
        Args:
            access_token: アクセストークン
            space_key: Backlogスペースキー
            
        Returns:
            ユーザー情報
            
        Raises:
            ExternalAPIException: ユーザー情報の取得に失敗した場合
            ValidationException: アクセスが許可されていない場合
        """
        # スペースのアクセス権限を検証
        BacklogAuthValidator.validate_space_access(space_key)
        
        logger.info("ユーザー情報を取得中...")
        user_info = await self.backlog_oauth_service.get_user_info(access_token, space_key=space_key)
        
        # ユーザー情報の追加検証（必要に応じて）
        BacklogAuthValidator.validate_user_status(user_info, space_key)
        
        return user_info
    
    def find_or_create_user(self, db: Session, user_info: dict) -> User:
        """
        ユーザーを検索または作成
        
        Args:
            db: データベースセッション
            user_info: Backlogから取得したユーザー情報
            
        Returns:
            Userオブジェクト
        """
        user = db.query(User).filter(User.backlog_id == user_info["id"]).first()
        
        if not user:
            # 新規ユーザーの作成
            logger.info(f"新規ユーザーを作成 - backlog_id: {user_info['id']}")
            user = User(
                backlog_id=user_info["id"],
                email=user_info.get("mailAddress"),
                name=user_info["name"],
                user_id=user_info["userId"],
                is_active=True,
                is_email_verified=True,  # Backlog OAuth認証済みユーザーは検証済みとする
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        else:
            logger.info(f"既存ユーザーを使用 - user_id: {user.id}")
            # 既存ユーザーの情報を更新
            user.email = user_info.get("mailAddress") or user.email
            user.name = user_info["name"]
            user.user_id = user_info["userId"]
            user.updated_at = datetime.now(timezone.utc)
            db.commit()
        
        return user
    
    def save_oauth_token(self, db: Session, user_id: int, token_data: dict, space_key: str, user_info: dict = None) -> None:
        """
        OAuthトークンを保存
        
        Args:
            db: データベースセッション
            user_id: ユーザーID
            token_data: トークンデータ
            space_key: Backlogスペースキー
            user_info: Backlogユーザー情報（オプション）
        """
        saved_token = self.backlog_oauth_service.save_token(db, user_id, token_data, space_key=space_key)
        
        # Backlogユーザー情報も保存（提供されている場合）
        if user_info and saved_token:
            saved_token.backlog_user_id = str(user_info.get("id", ""))
            saved_token.backlog_user_email = user_info.get("mailAddress", "")
            db.commit()
    
    def assign_default_role_if_needed(self, db: Session, user: User) -> User:
        """
        必要に応じてデフォルトロールを割り当て
        
        Args:
            db: データベースセッション
            user: ユーザーオブジェクト
            
        Returns:
            ロール情報を含むユーザーオブジェクト
        """
        # ユーザーのロール情報を取得
        user = QueryBuilder.with_user_roles(
            db.query(User).filter(User.id == user.id)
        ).first()
        
        # 新規ユーザーの場合、デフォルトロール（MEMBER）を割り当て
        if not user.user_roles:
            member_role = db.query(Role).filter(Role.name == "MEMBER").first()
            if member_role:
                user_role = UserRole(
                    user_id=user.id,
                    role_id=member_role.id,
                    project_id=None,  # グローバルロール
                    created_at=datetime.now(timezone.utc)
                )
                db.add(user_role)
                db.commit()
                db.refresh(user)
                # ロール情報を再取得
                user = QueryBuilder.with_user_roles(
                    db.query(User).filter(User.id == user.id)
                ).first()
        
        return user
    
    def create_jwt_tokens(self, user_id: int) -> Tuple[str, str]:
        """
        JWT認証トークンを生成
        
        Args:
            user_id: ユーザーID
            
        Returns:
            (アクセストークン, リフレッシュトークン)のタプル
        """
        access_token = create_access_token(data={"sub": str(user_id)})
        refresh_token = create_refresh_token(data={"sub": str(user_id)})
        return access_token, refresh_token
    
    def cleanup_oauth_state(self, db: Session, oauth_state: OAuthState) -> None:
        """
        使用済みのOAuthStateを削除
        
        Args:
            db: データベースセッション
            oauth_state: 削除するOAuthStateオブジェクト
        """
        db.delete(oauth_state)
        db.commit()