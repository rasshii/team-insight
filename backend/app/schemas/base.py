"""
Pydanticスキーマの基底クラス

すべてのスキーマが継承する基底クラスを定義し、
日時フィールドの自動的なJST変換を提供します。
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, field_serializer
from app.core.json_encoder import datetime_to_jst_str


class BaseSchema(BaseModel):
    """
    すべてのスキーマの基底クラス
    
    日時フィールドを自動的にJSTに変換してシリアライズします。
    """
    model_config = ConfigDict(
        from_attributes=True,  # SQLAlchemyモデルからの変換を許可
        json_encoders={
            datetime: datetime_to_jst_str  # datetimeをJSTに変換
        }
    )
    
    @field_serializer('created_at', 'updated_at', mode='plain', when_used='json')
    def serialize_datetime(self, dt: Optional[datetime]) -> Optional[str]:
        """日時フィールドをJSTに変換"""
        if dt is None:
            return None
        return datetime_to_jst_str(dt)


class TimestampMixin(BaseModel):
    """
    タイムスタンプフィールドを持つスキーマ用のMixin
    """
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    @field_serializer('created_at', 'updated_at', mode='plain', when_used='json')
    def serialize_timestamp(self, dt: Optional[datetime]) -> Optional[str]:
        """タイムスタンプをJSTに変換"""
        if dt is None:
            return None
        return datetime_to_jst_str(dt)