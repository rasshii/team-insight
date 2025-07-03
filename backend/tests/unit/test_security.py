"""
セキュリティ関連の単体テスト（JWT認証のみ）
"""
import pytest
from datetime import timedelta
from jose import jwt
from app.core.security import (
    create_access_token,
    decode_token
)
from app.core.config import settings


class TestJWTToken:
    """JWTトークン関連のテスト"""
    
    def test_create_access_token(self):
        """アクセストークンの生成"""
        data = {"sub": "123"}
        token = create_access_token(data=data)
        
        assert token is not None
        assert isinstance(token, str)
    
    def test_create_access_token_with_expires(self):
        """有効期限付きアクセストークンの生成"""
        data = {"sub": "123"}
        expires_delta = timedelta(minutes=15)
        token = create_access_token(data=data, expires_delta=expires_delta)
        
        decoded = jwt.decode(
            token, 
            settings.SECRET_KEY, 
            algorithms=["HS256"]
        )
        assert decoded["sub"] == "123"
        assert "exp" in decoded
    
    def test_decode_valid_token(self):
        """有効なトークンのデコード"""
        data = {"sub": "123", "email": "test@example.com"}
        token = create_access_token(data=data)
        
        decoded = decode_token(token)
        assert decoded["sub"] == "123"
        assert decoded["email"] == "test@example.com"
    
    def test_decode_expired_token(self):
        """期限切れトークンのデコード"""
        from fastapi import HTTPException
        
        data = {"sub": "123"}
        # 既に期限切れのトークンを作成
        token = create_access_token(
            data=data, 
            expires_delta=timedelta(minutes=-1)
        )
        
        # HTTPExceptionが発生することを確認
        with pytest.raises(HTTPException) as exc_info:
            decode_token(token)
        
        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == "無効な認証情報です"
    
    def test_decode_invalid_token(self):
        """無効なトークンのデコード"""
        from fastapi import HTTPException
        
        invalid_token = "invalid.token.here"
        
        # HTTPExceptionが発生することを確認
        with pytest.raises(HTTPException) as exc_info:
            decode_token(invalid_token)
        
        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == "無効な認証情報です"