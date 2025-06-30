"""
セキュリティ関連のユーティリティ

このモジュールは、JWT認証、パスワードハッシュ化、
ユーザー認証などのセキュリティ機能を提供します。
"""

from datetime import datetime, timedelta
from typing import Optional, Union
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db
from app.models.user import User

# パスワードハッシュ化のコンテキスト
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2スキーム
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token", auto_error=False)

# JWT設定
ALGORITHM = "HS256"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    パスワードを検証します

    Args:
        plain_password: 平文のパスワード
        hashed_password: ハッシュ化されたパスワード

    Returns:
        パスワードが一致する場合True
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    パスワードをハッシュ化します

    Args:
        password: 平文のパスワード

    Returns:
        ハッシュ化されたパスワード
    """
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    JWTアクセストークンを生成します

    Args:
        data: トークンに含めるデータ
        expires_delta: トークンの有効期限（デフォルトは設定値）

    Returns:
        JWTトークン
    """
    import logging
    logger = logging.getLogger(__name__)
    
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire, "type": "access"})
    logger.debug(f"Creating token with payload: {to_encode}, expire: {expire}")
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
    logger.debug(f"Created token: {encoded_jwt[:20]}...")
    return encoded_jwt


def create_refresh_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    JWTリフレッシュトークンを生成します

    Args:
        data: トークンに含めるデータ
        expires_delta: トークンの有効期限（デフォルトは設定値）

    Returns:
        JWTリフレッシュトークン
    """
    import logging
    logger = logging.getLogger(__name__)
    
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        # リフレッシュトークンはアクセストークンより長い有効期限を設定
        expire = datetime.utcnow() + timedelta(days=30)

    to_encode.update({"exp": expire, "type": "refresh"})
    logger.debug(f"Creating refresh token with payload: {to_encode}, expire: {expire}")
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
    logger.debug(f"Created refresh token: {encoded_jwt[:20]}...")
    return encoded_jwt


def decode_token(token: str) -> dict:
    """
    JWTトークンをデコードします

    Args:
        token: JWTトークン

    Returns:
        デコードされたペイロード

    Raises:
        HTTPException: トークンが無効な場合
    """
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        logger.debug(f"Decoding token: {token[:20]}...")
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        logger.debug(f"Decoded payload: {payload}")
        return payload
    except JWTError as e:
        logger.debug(f"JWT decode error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="無効な認証情報です",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user(
    request: Request,
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """
    現在のユーザーを取得します（オプショナル）

    Args:
        request: FastAPIリクエストオブジェクト
        token: JWTトークン（Authorizationヘッダーから）
        db: データベースセッション

    Returns:
        ユーザーオブジェクト（認証されていない場合はNone）
    """
    import logging
    logger = logging.getLogger(__name__)
    
    # デバッグ情報
    logger.debug(f"Authorization header token: {token}")
    logger.debug(f"Cookies: {request.cookies}")
    
    # まずCookieからトークンを取得を試みる
    if not token:
        token = request.cookies.get("auth_token")
        logger.debug(f"Token from cookie: {token}")
    
    if not token:
        logger.debug("No token found in header or cookie")
        return None

    try:
        payload = decode_token(token)
        logger.debug(f"Decoded payload: {payload}")
        user_id: str = payload.get("sub")
        if user_id is None:
            logger.debug("No 'sub' in payload")
            return None
    except HTTPException as e:
        logger.debug(f"Token decode error: {e.detail}")
        return None

    user = db.query(User).filter(User.id == int(user_id)).first()
    logger.debug(f"User found: {user.id if user else None}")
    return user


async def get_current_active_user(
    current_user: Optional[User] = Depends(get_current_user)
) -> User:
    """
    現在のアクティブユーザーを取得します（必須）

    Args:
        current_user: 現在のユーザー

    Returns:
        アクティブなユーザーオブジェクト

    Raises:
        HTTPException: ユーザーが認証されていない、または非アクティブな場合
    """
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="認証が必要です",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="非アクティブなユーザーです"
        )
    return current_user


async def get_current_active_superuser(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """
    現在のスーパーユーザーを取得します

    Args:
        current_user: 現在のアクティブユーザー

    Returns:
        スーパーユーザーオブジェクト

    Raises:
        HTTPException: ユーザーがスーパーユーザーでない場合
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="権限が不足しています"
        )
    return current_user


def verify_refresh_token(token: str) -> bool:
    """
    リフレッシュトークンを検証します

    Args:
        token: リフレッシュトークン

    Returns:
        トークンが有効な場合True
    """
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        # リフレッシュトークンであることを確認
        if payload.get("type") != "refresh":
            logger.debug("Token is not a refresh token")
            return False
        return True
    except JWTError as e:
        logger.debug(f"Refresh token verification failed: {str(e)}")
        return False


async def get_current_user_with_refresh_token(
    request: Request,
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """
    リフレッシュトークンから現在のユーザーを取得します

    Args:
        request: FastAPIリクエストオブジェクト
        token: リフレッシュトークン
        db: データベースセッション

    Returns:
        ユーザーオブジェクト

    Raises:
        HTTPException: トークンが無効な場合
    """
    import logging
    logger = logging.getLogger(__name__)
    
    # Cookieからリフレッシュトークンを取得を試みる
    refresh_token = request.cookies.get("refresh_token")
    
    if not refresh_token:
        # Authorizationヘッダーからトークンを取得
        if not token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="リフレッシュトークンが必要です",
                headers={"WWW-Authenticate": "Bearer"},
            )
        refresh_token = token
    
    try:
        payload = decode_token(refresh_token)
        # リフレッシュトークンであることを確認
        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="無効なトークンタイプです",
            )
        
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="無効なトークンです",
            )
    except HTTPException:
        raise
    
    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="ユーザーが見つかりません",
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="非アクティブなユーザーです"
        )
    
    return user
