"""
組織モデル (マルチテナント基盤)

Team Insight のマルチテナント分離を担う中核エンティティ。
1 インスタンスに複数の Organization が共存し、すべてのリソース
(projects / teams / tasks / notes / time_entries / evaluations 等) は
organization_id で分離される (アプリ層分離)。
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, CheckConstraint, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.db.base_class import BaseModel


class Organization(BaseModel):
    """
    組織モデル

    属性:
        name: 組織名 (表示用)
        slug: 組織識別子 (URL や Seed の参照キー、unique)
        fiscal_year_start_month: 年度開始月 (1-12)
        timezone: 組織のタイムゾーン (task_time_entries.logged_date 判定基準)
        settings: 組織別設定 (evaluation_weights など) を JSONB で保持
        is_active: 組織が有効か
        deleted_at: ソフトデリート用タイムスタンプ (NULL なら有効)

    Note:
        deleted_at を使ったソフトデリートを採用し、cascade ハードデリートは行わない。
        明示的なクリーンアップ API でリソースを削除する設計 (data loss 防止)。
    """

    __tablename__ = "organizations"
    __table_args__ = (
        UniqueConstraint("slug", name="uq_organizations_slug"),
        CheckConstraint(
            "fiscal_year_start_month BETWEEN 1 AND 12",
            name="ck_organizations_fiscal_year_start_month",
        ),
        {"schema": "team_insight"},
    )

    name = Column(String(100), nullable=False)
    slug = Column(String(50), nullable=False)
    fiscal_year_start_month = Column(Integer, nullable=False, default=4)
    timezone = Column(String(50), nullable=False, default="Asia/Tokyo")
    settings = Column(JSONB, nullable=False, default=dict)
    is_active = Column(Boolean, nullable=False, default=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    members = relationship(
        "OrganizationMember",
        back_populates="organization",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Organization(id={self.id}, slug={self.slug})>"
