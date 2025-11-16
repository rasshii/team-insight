"""
共通ユーティリティ関数
"""

from typing import Any, Dict, List, Optional, TypeVar, Generic, Callable
from datetime import datetime, timezone
import hashlib
import re
from functools import wraps
import time
import logging
from sqlalchemy.orm import Query, joinedload

logger = logging.getLogger(__name__)

T = TypeVar("T")


class QueryBuilder(Generic[T]):
    """
    SQLAlchemyクエリビルダーヘルパー

    共通のクエリパターンを簡潔に記述できるようにします
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
    def with_user_roles(query: Query) -> Query:
        """ユーザーロール情報を含めてロード"""
        from app.models.user import User
        from app.models.rbac import UserRole, Role

        return query.options(joinedload(User.user_roles).joinedload(UserRole.role))


def normalize_email(email: str) -> str:
    """
    メールアドレスを正規化

    Args:
        email: メールアドレス

    Returns:
        正規化されたメールアドレス
    """
    return email.strip().lower()


def generate_hash(value: str, salt: Optional[str] = None) -> str:
    """
    文字列のハッシュを生成

    Args:
        value: ハッシュ化する文字列
        salt: ソルト（オプション）

    Returns:
        ハッシュ値
    """
    if salt:
        value = f"{salt}{value}"
    return hashlib.sha256(value.encode()).hexdigest()


def sanitize_filename(filename: str) -> str:
    """
    ファイル名をサニタイズ

    Args:
        filename: ファイル名

    Returns:
        安全なファイル名
    """
    # 危険な文字を除去
    filename = re.sub(r"[^\w\s.-]", "", filename)
    # 空白をアンダースコアに置換
    filename = re.sub(r"\s+", "_", filename)
    # 連続するピリオドを単一に
    filename = re.sub(r"\.+", ".", filename)
    return filename


def get_current_utc_time() -> datetime:
    """現在のUTC時刻を取得"""
    return datetime.now(timezone.utc)


def format_datetime(dt: datetime, format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
    """
    日時を指定されたフォーマットで文字列化

    Args:
        dt: 日時
        format_str: フォーマット文字列

    Returns:
        フォーマットされた日時文字列
    """
    return dt.strftime(format_str)


def parse_bool(value: Any) -> bool:
    """
    様々な値をboolに変換

    Args:
        value: 変換する値

    Returns:
        bool値
    """
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() in ("true", "yes", "1", "on")
    return bool(value)


def chunks(lst: List[T], n: int) -> List[List[T]]:
    """
    リストをn個ずつのチャンクに分割

    Args:
        lst: 分割するリスト
        n: チャンクサイズ

    Yields:
        チャンク
    """
    for i in range(0, len(lst), n):
        yield lst[i : i + n]


def retry_on_exception(
    max_retries: int = 3, delay: float = 1.0, backoff: float = 2.0, exceptions: tuple = (Exception,)
) -> Callable:
    """
    例外発生時にリトライするデコレータ

    Args:
        max_retries: 最大リトライ回数
        delay: 初回リトライまでの待機時間（秒）
        backoff: リトライごとの待機時間の倍率
        exceptions: リトライ対象の例外タプル

    Returns:
        デコレータ関数
    """

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
                        logger.error(f"Max retries ({max_retries}) exceeded for {func.__name__}. " f"Last error: {str(e)}")

            if last_exception:
                raise last_exception

        return wrapper

    return decorator


def safe_get(dictionary: Dict[str, Any], keys: List[str], default: Any = None) -> Any:
    """
    ネストされた辞書から安全に値を取得

    Args:
        dictionary: 辞書
        keys: キーのリスト
        default: デフォルト値

    Returns:
        取得した値またはデフォルト値
    """
    result = dictionary
    for key in keys:
        if isinstance(result, dict) and key in result:
            result = result[key]
        else:
            return default
    return result


def merge_dicts(dict1: Dict[str, Any], dict2: Dict[str, Any]) -> Dict[str, Any]:
    """
    2つの辞書を再帰的にマージ

    Args:
        dict1: ベース辞書
        dict2: マージする辞書

    Returns:
        マージされた辞書
    """
    result = dict1.copy()

    for key, value in dict2.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = merge_dicts(result[key], value)
        else:
            result[key] = value

    return result


def calculate_percentage(current: float, total: float, decimals: int = 2) -> float:
    """
    パーセンテージを計算

    Args:
        current: 現在値
        total: 総数
        decimals: 小数点以下の桁数

    Returns:
        パーセンテージ
    """
    if total == 0:
        return 0.0
    return round((current / total) * 100, decimals)


def truncate_string(text: str, max_length: int, suffix: str = "...") -> str:
    """
    文字列を指定長で切り詰め

    Args:
        text: 対象文字列
        max_length: 最大長
        suffix: 末尾に付ける文字列

    Returns:
        切り詰められた文字列
    """
    if len(text) <= max_length:
        return text
    return text[: max_length - len(suffix)] + suffix


def build_user_role_responses(user_roles: List[Any]) -> List[Dict[str, Any]]:
    """
    UserRoleモデルのリストをレスポンス形式に変換

    Args:
        user_roles: UserRoleモデルのリスト

    Returns:
        UserRoleResponseの形式に変換されたリスト
    """
    from app.schemas.auth import UserRoleResponse, RoleResponse

    responses = []
    for user_role in user_roles:
        role_data = RoleResponse(id=user_role.role.id, name=user_role.role.name, description=user_role.role.description)

        user_role_data = UserRoleResponse(
            id=user_role.id, role_id=user_role.role_id, project_id=user_role.project_id, role=role_data
        )

        responses.append(user_role_data.model_dump())

    return responses
