"""
共通ユーティリティ関数 (Phase 0: organization_memberships ベースに更新)
"""

import hashlib
import logging
import re
import time
from datetime import datetime, timezone
from functools import wraps
from typing import Any, Callable, Dict, Generic, List, Optional, TypeVar

from sqlalchemy.orm import Query, joinedload

logger = logging.getLogger(__name__)

T = TypeVar("T")


class QueryBuilder(Generic[T]):
    """
    SQLAlchemy クエリビルダーヘルパー

    共通のクエリパターンを簡潔に記述できるようにする。
    """

    def __init__(self, query: Query):
        self.query = query

    def filter_if(self, condition: bool, *args, **kwargs) -> "QueryBuilder[T]":
        """条件が真の場合のみフィルタを適用"""
        if condition:
            self.query = self.query.filter(*args, **kwargs)
        return self

    def order_by_if(self, condition: bool, *args) -> "QueryBuilder[T]":
        """条件が真の場合のみ並び順を適用"""
        if condition:
            self.query = self.query.order_by(*args)
        return self

    def paginate(self, page: int = 1, per_page: int = 20) -> "QueryBuilder[T]":
        """ページネーションを適用"""
        offset = (page - 1) * per_page
        self.query = self.query.limit(per_page).offset(offset)
        return self

    def build(self) -> Query:
        """最終的なクエリを返す"""
        return self.query

    @staticmethod
    def with_organization_memberships(query: Query) -> Query:
        """ユーザーの organization_memberships を eager load する"""
        from app.models.organization_member import OrganizationMember
        from app.models.user import User

        return query.options(
            joinedload(User.organization_memberships).joinedload(
                OrganizationMember.organization
            )
        )


def normalize_email(email: str) -> str:
    """メールアドレスを正規化"""
    return email.strip().lower()


def generate_hash(value: str, salt: Optional[str] = None) -> str:
    """文字列のハッシュを生成"""
    if salt:
        value = f"{salt}{value}"
    return hashlib.sha256(value.encode()).hexdigest()


def sanitize_filename(filename: str) -> str:
    """ファイル名をサニタイズ"""
    filename = re.sub(r"[^\w\s.-]", "", filename)
    filename = re.sub(r"\s+", "_", filename)
    filename = re.sub(r"\.+", ".", filename)
    return filename


def get_current_utc_time() -> datetime:
    """現在の UTC 時刻を取得"""
    return datetime.now(timezone.utc)


def format_datetime(dt: datetime, format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
    """日時を指定されたフォーマットで文字列化"""
    return dt.strftime(format_str)


def parse_bool(value: Any) -> bool:
    """様々な値を bool に変換"""
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() in ("true", "yes", "1", "on")
    return bool(value)


def chunks(lst: List[T], n: int) -> List[List[T]]:
    """リストを n 個ずつのチャンクに分割"""
    for i in range(0, len(lst), n):
        yield lst[i : i + n]


def retry_on_exception(
    max_retries: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple = (Exception,),
) -> Callable:
    """例外発生時にリトライするデコレータ"""

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            current_delay = delay
            last_exception = None

            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_retries:
                        logger.warning(
                            f"Retry {attempt + 1}/{max_retries} for {func.__name__} "
                            f"after {current_delay}s delay. Error: {str(e)}"
                        )
                        time.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        logger.error(
                            f"Max retries ({max_retries}) exceeded for {func.__name__}. "
                            f"Last error: {str(e)}"
                        )

            if last_exception:
                raise last_exception

        return wrapper

    return decorator


def safe_get(dictionary: Dict[str, Any], keys: List[str], default: Any = None) -> Any:
    """ネストされた辞書から安全に値を取得"""
    result = dictionary
    for key in keys:
        if isinstance(result, dict) and key in result:
            result = result[key]
        else:
            return default
    return result


def merge_dicts(dict1: Dict[str, Any], dict2: Dict[str, Any]) -> Dict[str, Any]:
    """2 つの辞書を再帰的にマージ"""
    result = dict1.copy()

    for key, value in dict2.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = merge_dicts(result[key], value)
        else:
            result[key] = value

    return result


def calculate_percentage(current: float, total: float, decimals: int = 2) -> float:
    """パーセンテージを計算"""
    if total == 0:
        return 0.0
    return round((current / total) * 100, decimals)


def truncate_string(text: str, max_length: int, suffix: str = "...") -> str:
    """文字列を指定長で切り詰め"""
    if len(text) <= max_length:
        return text
    return text[: max_length - len(suffix)] + suffix


def build_organization_membership_responses(
    memberships: List[Any],
) -> List[Dict[str, Any]]:
    """
    OrganizationMember モデルのリストをレスポンス形式に変換

    Args:
        memberships: OrganizationMember モデルのリスト

    Returns:
        organization_id / organization_name / role を含む辞書リスト
    """
    responses = []
    for membership in memberships:
        responses.append(
            {
                "organization_id": membership.organization_id,
                "organization_name": getattr(membership.organization, "name", None),
                "organization_slug": getattr(membership.organization, "slug", None),
                "role": membership.role,
                "joined_at": membership.joined_at.isoformat()
                if membership.joined_at
                else None,
            }
        )
    return responses
