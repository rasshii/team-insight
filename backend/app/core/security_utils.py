"""
セキュリティ関連のユーティリティ関数
"""

import re
import secrets
import string
from typing import Optional, Tuple
from datetime import datetime, timedelta, timezone
import logging


logger = logging.getLogger(__name__)


class TokenGenerator:
    """セキュアなトークン生成クラス"""

    @staticmethod
    def generate_secure_token(length: int = 32) -> str:
        """
        セキュアなトークンを生成

        Args:
            length: トークンの長さ（バイト数）

        Returns:
            生成されたトークン
        """
        return secrets.token_urlsafe(length)

    @staticmethod
    def generate_numeric_code(length: int = 6) -> str:
        """
        数値のみの確認コードを生成

        Args:
            length: コードの長さ

        Returns:
            生成されたコード
        """
        return "".join(secrets.choice(string.digits) for _ in range(length))

    @staticmethod
    def generate_api_key() -> str:
        """
        APIキーを生成

        Returns:
            生成されたAPIキー
        """
        prefix = "ti_"  # Team Insightのプレフィックス
        key = secrets.token_urlsafe(32)
        return f"{prefix}{key}"


class RateLimiter:
    """レート制限ヘルパークラス"""

    ATTEMPT_LIMITS = {
        "login": (5, 300),  # 5回/5分
        "api_key_generation": (10, 86400),  # 10回/1日
    }

    @classmethod
    def get_limit_key(cls, action: str, identifier: str) -> str:
        """
        レート制限用のキーを生成

        Args:
            action: アクション名
            identifier: 識別子（IPアドレス、ユーザーIDなど）

        Returns:
            キー
        """
        return f"rate_limit:{action}:{identifier}"

    @classmethod
    def get_limits(cls, action: str) -> Tuple[int, int]:
        """
        アクションのレート制限を取得

        Args:
            action: アクション名

        Returns:
            (最大試行回数, 時間枠（秒）)のタプル
        """
        return cls.ATTEMPT_LIMITS.get(action, (10, 60))


def sanitize_input(text: str, max_length: Optional[int] = None) -> str:
    """
    入力テキストをサニタイズ

    Args:
        text: サニタイズするテキスト
        max_length: 最大長

    Returns:
        サニタイズされたテキスト
    """
    # 制御文字を除去
    text = re.sub(r"[\x00-\x1F\x7F-\x9F]", "", text)

    # 前後の空白を除去
    text = text.strip()

    # 最大長でカット
    if max_length and len(text) > max_length:
        text = text[:max_length]

    return text


def is_safe_redirect_url(url: str, allowed_hosts: Optional[list] = None) -> bool:
    """
    リダイレクトURLが安全かチェック

    Args:
        url: チェックするURL
        allowed_hosts: 許可されたホストのリスト

    Returns:
        安全性
    """
    if not url:
        return False

    # 相対URLは許可
    if url.startswith("/") and not url.startswith("//"):
        return True

    # 許可されたホストをチェック
    if allowed_hosts:
        from urllib.parse import urlparse

        parsed = urlparse(url)
        return parsed.hostname in allowed_hosts

    return False


def mask_sensitive_data(data: str, visible_chars: int = 4) -> str:
    """
    機密データをマスク

    Args:
        data: マスクするデータ
        visible_chars: 表示する文字数

    Returns:
        マスクされたデータ
    """
    if not data or len(data) <= visible_chars:
        return "*" * 8

    return data[:visible_chars] + "*" * (len(data) - visible_chars)
