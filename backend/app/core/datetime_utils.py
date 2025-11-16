"""
日時処理ユーティリティ

このモジュールは、アプリケーション全体で一貫した日時処理を提供します。
基本方針：
- データベースにはUTC（タイムゾーン付き）で保存
- APIレスポンスでは日本時間（JST）に変換
- 内部処理はすべてタイムゾーン付きdatetimeを使用
"""

from datetime import datetime, timezone, timedelta
from typing import Optional, Union
from zoneinfo import ZoneInfo

# タイムゾーン定義
UTC = timezone.utc
JST = ZoneInfo("Asia/Tokyo")


def get_current_time() -> datetime:
    """
    現在時刻をUTCタイムゾーン付きで取得

    Returns:
        datetime: UTCタイムゾーン付きの現在時刻
    """
    return datetime.now(UTC)


def get_current_time_jst() -> datetime:
    """
    現在時刻を日本時間（JST）で取得

    Returns:
        datetime: JSTタイムゾーン付きの現在時刻
    """
    return datetime.now(JST)


def to_jst(dt: Optional[datetime]) -> Optional[datetime]:
    """
    datetimeを日本時間に変換

    Args:
        dt: 変換するdatetime（naive/awareどちらでも可）

    Returns:
        JSTタイムゾーン付きdatetime、またはNone
    """
    if dt is None:
        return None

    # naiveな場合はUTCとして扱う
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)

    return dt.astimezone(JST)


def to_utc(dt: Optional[datetime]) -> Optional[datetime]:
    """
    datetimeをUTCに変換

    Args:
        dt: 変換するdatetime（naive/awareどちらでも可）

    Returns:
        UTCタイムゾーン付きdatetime、またはNone
    """
    if dt is None:
        return None

    # naiveな場合はローカルタイムとして扱う
    if dt.tzinfo is None:
        # 警告: naiveなdatetimeは避けるべき
        dt = dt.replace(tzinfo=UTC)

    return dt.astimezone(UTC)


def ensure_timezone_aware(dt: Optional[datetime], tz: timezone = UTC) -> Optional[datetime]:
    """
    datetimeがタイムゾーン付きであることを保証

    Args:
        dt: チェックするdatetime
        tz: naiveな場合に適用するタイムゾーン（デフォルト: UTC）

    Returns:
        タイムゾーン付きdatetime、またはNone
    """
    if dt is None:
        return None

    if dt.tzinfo is None:
        return dt.replace(tzinfo=tz)

    return dt


def format_datetime_jst(dt: Optional[datetime], format: str = "%Y-%m-%d %H:%M:%S") -> str:
    """
    datetimeを日本時間でフォーマット

    Args:
        dt: フォーマットするdatetime
        format: 日時フォーマット文字列

    Returns:
        フォーマットされた日時文字列、またはdtがNoneの場合は空文字列
    """
    if dt is None:
        return ""

    jst_dt = to_jst(dt)
    return jst_dt.strftime(format) if jst_dt else ""


def parse_datetime(dt_str: str, tz: Optional[Union[timezone, ZoneInfo]] = UTC) -> datetime:
    """
    ISO形式の文字列をdatetimeに変換

    Args:
        dt_str: ISO形式の日時文字列
        tz: タイムゾーン情報がない場合に適用するタイムゾーン

    Returns:
        datetime: パースされたdatetime

    Raises:
        ValueError: パースに失敗した場合
    """
    try:
        dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
    except ValueError:
        # ISO形式でない場合の基本的なパース
        dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S")

    return ensure_timezone_aware(dt, tz)


def add_hours(dt: datetime, hours: int) -> datetime:
    """
    datetimeに時間を加算（タイムゾーンを保持）

    Args:
        dt: 基準となるdatetime
        hours: 加算する時間数

    Returns:
        時間が加算されたdatetime
    """
    return dt + timedelta(hours=hours)


def is_expired(dt: Optional[datetime]) -> bool:
    """
    指定された日時が現在時刻より過去かどうかをチェック

    Args:
        dt: チェックする日時

    Returns:
        期限切れの場合True、そうでない場合またはdtがNoneの場合False
    """
    if dt is None:
        return False

    # タイムゾーンを揃えて比較
    dt = ensure_timezone_aware(dt)
    return dt < get_current_time()


# SQLAlchemy用のデフォルト値生成関数
def utcnow() -> datetime:
    """
    SQLAlchemyのdefault引数用の現在UTC時刻取得関数

    Returns:
        UTCタイムゾーン付きの現在時刻
    """
    return get_current_time()


# 既存コードとの互換性のためのエイリアス
def get_current_utc_time() -> datetime:
    """
    現在のUTC時刻を取得（既存コードとの互換性用）

    Returns:
        UTCタイムゾーン付きの現在時刻
    """
    return get_current_time()
