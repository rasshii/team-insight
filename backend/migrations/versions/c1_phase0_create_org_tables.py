"""Phase 0: Create organizations and organization_members tables, add is_system_admin to users

マルチテナント基盤の中核となる以下を導入する:
- organizations: 組織エンティティ (slug ユニーク、settings JSONB、soft delete)
- organization_members: User × Organization の M:M 関連 + ロール (ADMIN/PROJECT_LEADER/MEMBER)
- users.is_system_admin: System Admin フラグ (テナントバイパス用)

初期組織 "default" を Seed する (Phase 1 で初期 admin user を seed_default_org スクリプトで投入)。

Revision ID: c1_phase0_create_org_tables
Revises: b3_phase7_drop_user_proj_backlog
Create Date: 2026-05-06 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'c1_phase0_create_org_tables'
down_revision: Union[str, None] = 'b3_phase7_drop_user_proj_backlog'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # organizations テーブル作成
    op.create_table(
        'organizations',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('slug', sa.String(length=50), nullable=False),
        sa.Column('fiscal_year_start_month', sa.Integer(), nullable=False, server_default=sa.text('4')),
        sa.Column('timezone', sa.String(length=50), nullable=False, server_default=sa.text("'Asia/Tokyo'")),
        sa.Column(
            'settings',
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint('slug', name='uq_organizations_slug'),
        sa.CheckConstraint(
            'fiscal_year_start_month BETWEEN 1 AND 12',
            name='ck_organizations_fiscal_year_start_month',
        ),
        schema='team_insight',
    )

    # users.is_system_admin カラム追加
    op.add_column(
        'users',
        sa.Column('is_system_admin', sa.Boolean(), nullable=False, server_default=sa.false()),
        schema='team_insight',
    )

    # organization_members テーブル作成
    op.create_table(
        'organization_members',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column(
            'organization_id',
            sa.Integer(),
            sa.ForeignKey('team_insight.organizations.id', ondelete='CASCADE'),
            nullable=False,
        ),
        sa.Column(
            'user_id',
            sa.Integer(),
            sa.ForeignKey('team_insight.users.id', ondelete='CASCADE'),
            nullable=False,
        ),
        sa.Column('role', sa.String(length=20), nullable=False, server_default=sa.text("'MEMBER'")),
        sa.Column('joined_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint('organization_id', 'user_id', name='uq_org_members_org_user'),
        sa.CheckConstraint(
            "role IN ('ADMIN', 'PROJECT_LEADER', 'MEMBER')",
            name='ck_org_members_role',
        ),
        schema='team_insight',
    )
    op.create_index(
        'idx_org_members_user', 'organization_members', ['user_id'], schema='team_insight'
    )

    # 初期組織 "default" を Seed (環境変数 INITIAL_ORGANIZATION_NAME で上書き可能だが Phase 0 では固定)
    op.execute(
        """
        INSERT INTO team_insight.organizations (name, slug, fiscal_year_start_month, timezone, settings, is_active)
        VALUES ('Default Organization', 'default', 4, 'Asia/Tokyo', '{}'::jsonb, true)
        """
    )


def downgrade() -> None:
    op.drop_index(
        'idx_org_members_user', table_name='organization_members', schema='team_insight'
    )
    op.drop_table('organization_members', schema='team_insight')
    op.drop_column('users', 'is_system_admin', schema='team_insight')
    op.drop_table('organizations', schema='team_insight')
