"""
認証関連のAPIエンドポイント

このモジュールは、OAuth2.0認証フローのためのAPIエンドポイントを提供します。
認証URLの生成、コールバック処理、トークンのリフレッシュなどを処理します。
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import RedirectResponse, JSONResponse
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Optional
import logging
from zoneinfo import ZoneInfo

from app.db.session import get_db
from app.services.backlog_oauth import backlog_oauth_service
from app.models.auth import OAuthState
from app.schemas.auth import (
    AuthorizationResponse,
    TokenResponse,
    CallbackRequest,
    UserInfoResponse,
)
from app.core.security import get_current_user, get_current_active_user
from app.models.user import User

router = APIRouter()


@router.get("/backlog/authorize", response_model=AuthorizationResponse)
async def get_authorization_url(
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user),
):
    """
    Backlog OAuth2.0認証URLを生成します

    このエンドポイントは、ユーザーをBacklogの認証ページにリダイレクトするための
    URLを生成します。CSRF攻撃を防ぐため、stateパラメータも生成して保存します。

    Returns:
        認証URLとstateを含むレスポンス
    """
    try:
        # 認証URLとstateを生成
        auth_url, state = backlog_oauth_service.get_authorization_url()

        # stateをデータベースに保存（10分間有効）
        expires_at = datetime.now(ZoneInfo("Asia/Tokyo")) + timedelta(minutes=10)
        oauth_state = OAuthState(
            state=state,
            user_id=current_user.id if current_user else None,
            expires_at=expires_at,
        )
        db.add(oauth_state)
        db.commit()

        return AuthorizationResponse(authorization_url=auth_url, state=state)
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"認証URLの生成に失敗しました: {str(e)}"
        )


@router.post("/backlog/callback", response_model=TokenResponse)
async def handle_callback(request: CallbackRequest, db: Session = Depends(get_db)):
    """
    Backlog OAuth2.0認証のコールバックを処理します

    Backlogから認証コードを受け取り、アクセストークンに交換します。
    また、CSRF攻撃を防ぐためstateパラメータを検証します。

    Args:
        request: 認証コードとstateを含むリクエスト

    Returns:
        アクセストークンとユーザー情報を含むレスポンス

    Raises:
        HTTPException: state検証失敗またはトークン取得失敗時
    """
    logger = logging.getLogger(__name__)

    logger.info(
        f"認証コールバック開始 - code: {request.code[:10]}..., state: {request.state}"
    )

    # stateの検証
    oauth_state = db.query(OAuthState).filter(OAuthState.state == request.state).first()

    if not oauth_state:
        logger.error(f"無効なstateパラメータ - state: {request.state}")
        # デバッグ用：現在のstateをすべて表示
        all_states = db.query(OAuthState).all()
        logger.debug(f"現在のstate一覧: {[s.state for s in all_states]}")
        raise HTTPException(status_code=400, detail="無効なstateパラメータです")

    if oauth_state.is_expired():
        logger.error(f"stateパラメータの有効期限切れ - state: {request.state}")
        db.delete(oauth_state)
        db.commit()
        raise HTTPException(
            status_code=400, detail="stateパラメータの有効期限が切れています"
        )

    try:
        # 認証コードをアクセストークンに交換
        logger.info("認証コードをアクセストークンに交換中...")
        token_data = await backlog_oauth_service.exchange_code_for_token(request.code)

        # ユーザー情報を取得
        logger.info("ユーザー情報を取得中...")
        user_info = await backlog_oauth_service.get_user_info(
            token_data["access_token"]
        )

        # ユーザーの作成または更新
        user = db.query(User).filter(User.backlog_id == user_info["id"]).first()
        if not user:
            # 新規ユーザーの作成
            logger.info(f"新規ユーザーを作成 - backlog_id: {user_info['id']}")
            user = User(
                backlog_id=user_info["id"],
                email=user_info.get("mailAddress"),
                name=user_info["name"],
                user_id=user_info["userId"],
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        else:
            logger.info(f"既存ユーザーを使用 - user_id: {user.id}")

        # トークンを保存
        backlog_oauth_service.save_token(db, user.id, token_data)

        # 使用済みのstateを削除
        db.delete(oauth_state)
        db.commit()

        # JWTトークンを生成（アプリケーション内での認証用）
        from app.core.security import create_access_token

        access_token = create_access_token(data={"sub": str(user.id)})

        logger.info(f"認証コールバック成功 - user_id: {user.id}")

        # レスポンスを作成
        response = TokenResponse(
            access_token=access_token,
            token_type="bearer",
            user=UserInfoResponse(
                id=user.id,
                backlog_id=user.backlog_id,
                email=user.email,
                name=user.name,
                user_id=user.user_id,
            ),
        )

        # Set-Cookieヘッダーを設定
        return JSONResponse(
            content=response.model_dump(),
            headers={
                "Set-Cookie": f"auth_token={access_token}; Path=/; HttpOnly; SameSite=Lax; Max-Age=604800"
            },
        )

    except Exception as e:
        logger.error(f"認証処理エラー: {str(e)}", exc_info=True)
        # エラー時はstateを削除
        db.delete(oauth_state)
        db.commit()
        raise HTTPException(status_code=500, detail=f"認証処理に失敗しました: {str(e)}")


@router.post("/backlog/refresh", response_model=TokenResponse)
async def refresh_token(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    """
    Backlogのアクセストークンをリフレッシュします

    保存されているリフレッシュトークンを使用して、
    新しいアクセストークンを取得します。

    Returns:
        新しいアクセストークンを含むレスポンス

    Raises:
        HTTPException: トークンが見つからない、またはリフレッシュ失敗時
    """
    # ユーザーのBacklogトークンを取得
    from app.models.auth import OAuthToken

    oauth_token = (
        db.query(OAuthToken)
        .filter(OAuthToken.user_id == current_user.id, OAuthToken.provider == "backlog")
        .first()
    )

    if not oauth_token:
        raise HTTPException(status_code=404, detail="Backlogトークンが見つかりません")

    try:
        # トークンをリフレッシュ
        new_token_data = await backlog_oauth_service.refresh_access_token(
            oauth_token.refresh_token
        )

        # 新しいトークンを保存
        backlog_oauth_service.save_token(db, current_user.id, new_token_data)

        # アプリケーション用のJWTトークンも新しく生成
        from app.core.security import create_access_token

        access_token = create_access_token(data={"sub": str(current_user.id)})

        # レスポンスを作成
        response = TokenResponse(
            access_token=access_token,
            token_type="bearer",
            user=UserInfoResponse(
                id=current_user.id,
                backlog_id=current_user.backlog_id,
                email=current_user.email,
                name=current_user.name,
                user_id=current_user.user_id,
            ),
        )

        # Set-Cookieヘッダーを設定
        return JSONResponse(
            content=response.model_dump(),
            headers={
                "Set-Cookie": f"auth_token={access_token}; Path=/; HttpOnly; SameSite=Lax; Max-Age=604800"
            },
        )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"トークンのリフレッシュに失敗しました: {str(e)}"
        )


@router.get("/verify", response_model=UserInfoResponse)
async def verify_token(current_user: User = Depends(get_current_user)):
    """
    JWTトークンの有効性を確認し、ユーザー情報を返す
    
    このエンドポイントは、フロントエンドのミドルウェアから呼び出され、
    トークンが有効かどうかを確認するために使用されます。
    """
    if not current_user:
        raise HTTPException(
            status_code=401,
            detail="認証が必要です",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return UserInfoResponse(
        id=current_user.id,
        backlog_id=current_user.backlog_id,
        email=current_user.email,
        name=current_user.name,
        user_id=current_user.user_id,
    )


@router.get("/me", response_model=UserInfoResponse)
async def get_current_user_info(current_user: User = Depends(get_current_active_user)):
    """
    現在ログイン中のユーザー情報を取得します

    Returns:
        ユーザー情報
    """
    return UserInfoResponse(
        id=current_user.id,
        backlog_id=current_user.backlog_id,
        email=current_user.email,
        name=current_user.name,
        user_id=current_user.user_id,
    )
