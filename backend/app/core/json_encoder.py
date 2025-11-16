"""
カスタムJSONエンコーダー

日時データを日本時間（JST）に変換してシリアライズします。
"""

import json
from datetime import datetime
from typing import Any
from app.core.datetime_utils import to_jst, format_datetime_jst


class JSTJSONEncoder(json.JSONEncoder):
    """
    日時を日本時間に変換するJSONエンコーダー
    """

    def default(self, obj: Any) -> Any:
        if isinstance(obj, datetime):
            # 日本時間に変換してISO形式で出力
            jst_dt = to_jst(obj)
            if jst_dt:
                # ISO形式に"+09:00"のタイムゾーン情報を含める
                return jst_dt.isoformat()
            return None

        return super().default(obj)


def datetime_to_jst_str(dt: datetime) -> str:
    """
    Pydanticのfield_serializer用のヘルパー関数

    Args:
        dt: 変換するdatetime

    Returns:
        JST形式の文字列
    """
    jst_dt = to_jst(dt)
    return jst_dt.isoformat() if jst_dt else ""
