"""
セキュリティ関連のユーティリティ (Phase 0: JWT に active_org_id + jti を埋め込み)

このモジュールは、Team InsightアプリケーションのセキュリティとJWT認証機能を提供します。

主要な機能:
    1. JWT (JSON Web Token) トークンの生成と検証
       - アクセストークン: 短期間有効 (デフォルト15分)
       - リフレッシュトークン: 長期間有効 (デフォルト30日)
       - sub (user_id), active_org_id, is_system_admin, jti (refresh のみ) を含む

    2. パスワードハッシュ (Phase 1 で本格利用)
       - bcrypt によるハッシュ化と検証

    3. JWT 失効リスト連携
       - 組織切替・ログアウト時に refresh token を失効させる
"""

import logging
import uuid
from datetime import datetime, timedelta
from typing import Any, Optional

from fastapi import HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

logger = logging.getLogger(__name__)

# OAuth2 スキーム
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token", auto_error=False)

# JWT 設定
ALGORITHM = "HS256"

# パスワードハッシュコンテキスト (Phase 1 のローカル認証で利用)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain_password: str) -> str:
    """平文パスワードを bcrypt でハッシュ化"""
    return pwd_context.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """平文パスワードがハッシュと一致するか検証"""
    return pwd_context.verify(plain_password, hashed_password)


def _build_token_payload(
    user_id: int,
    *,
    active_org_id: Optional[int],
    is_system_admin: bool,
    extra: Optional[dict] = None,
) -> dict:
    """JWT ペイロードの共通部を構築"""
    payload: dict[str, Any] = {
        "sub": str(user_id),
        "active_org_id": active_org_id,
        "is_system_admin": is_system_admin,
    }
    if extra:
        payload.update(extra)
    return payload


def create_access_token(
    user_id: int,
    *,
    active_org_id: Optional[int] = None,
    is_system_admin: bool = False,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """
    アクセストークンを生成

    Args:
        user_id: ユーザー ID (sub クレーム)
        active_org_id: 現在アクティブな組織 ID (組織切替時に変更される)
        is_system_admin: System Admin フラグ
        expires_delta: 有効期限 (デフォルト: settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    Returns:
        署名済 JWT 文字列
    """
    expire = datetime.utcnow() + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    payload = _build_token_payload(
        user_id,
        active_org_id=active_org_id,
        is_system_admin=is_system_admin,
        extra={"exp": expire, "type": "access"},
    )
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=ALGORITHM)


def create_refresh_token(
    user_id: int,
    *,
    active_org_id: Optional[int] = None,
    is_system_admin: bool = False,
    expires_delta: Optional[timedelta] = None,
) -> tuple[str, str]:
    """
    リフレッシュトークンを生成

    Returns:
        (token, jti) のタプル。jti は失効リスト登録用に呼び出し側で保持する。
    """
    expire = datetime.utcnow() + (
        expires_delta or timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    )
    jti = str(uuid.uuid4())
    payload = _build_token_payload(
        user_id,
        active_org_id=active_org_id,
        is_system_admin=is_system_admin,
        extra={"exp": expire, "type": "refresh", "jti": jti},
    )
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm=ALGORITHM)
    return token, jti


def decode_token(token: str) -> dict:
    """
    JWT を検証してペイロードを返す。失敗時は 401。

    Returns:
        dict: ペイロード (sub, exp, type, active_org_id, is_system_admin, jti?)
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError as e:
        logger.debug(f"JWT decode error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="無効な認証情報です",
            headers={"WWW-Authenticate": "Bearer"},
        )


def verify_refresh_token(token: str) -> bool:
    """
    リフレッシュトークンが形式・署名・期限・type を満たすか (失効リストは別途チェック)

    Returns:
        bool: 有効なら True
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        return payload.get("type") == "refresh"
    except JWTError:
        return False


def calculate_remaining_seconds(payload: dict) -> int:
    """ペイロードの exp から残有効秒数を計算 (失効リスト TTL 計算用)"""
    exp = payload.get("exp")
    if not exp:
        return 0
    remaining = int(exp - datetime.utcnow().timestamp())
    return max(0, remaining)
