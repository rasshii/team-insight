"""Phase 0: Drop legacy RBAC tables (user_roles, role_permissions, roles, permissions)

旧 RBAC テーブルを廃止し、organization_members.role + users.is_system_admin に
権限管理を一本化する (MIGRATION_PLAN.md / docs/MIGRATION_PLAN.md Phase 7 RBAC 統合)。

Phase 7 (b3) で関連データは既に DELETE 済みのため、ここでは DROP のみ実施。

Revision ID: c3_phase0_drop_rbac_tables
Revises: c2_phase0_add_organization_id
Create Date: 2026-05-06 10:20:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c3_phase0_drop_rbac_tables'
down_revision: Union[str, None] = 'c2_phase0_add_organization_id'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 念のため残存データを削除 (b3 で実施済だが冪等性確保)
    op.execute("DELETE FROM team_insight.user_roles")
    op.execute("DELETE FROM team_insight.role_permissions")
    op.execute("DELETE FROM team_insight.permissions")
    op.execute("DELETE FROM team_insight.roles")

    # 子テーブルから DROP (FK 依存順)
    op.drop_table('user_roles', schema='team_insight')
    op.drop_table('role_permissions', schema='team_insight')
    op.drop_table('permissions', schema='team_insight')
    op.drop_table('roles', schema='team_insight')


def downgrade() -> None:
    # 旧 RBAC スキーマを復元 (元の構造を再現、データは復元できない)
    op.create_table(
        'roles',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('name', sa.String(length=50), nullable=False),
        sa.Column('description', sa.String(length=255), nullable=True),
        sa.Column('is_system', sa.Boolean(), server_default=sa.false()),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint('name', name='roles_name_key'),
        schema='team_insight',
    )
    op.create_index('ix_team_insight_roles_name', 'roles', ['name'], unique=True, schema='team_insight')

    op.create_table(
        'permissions',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('resource', sa.String(length=50), nullable=False),
        sa.Column('action', sa.String(length=50), nullable=False),
        sa.Column('description', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint('name', name='permissions_name_key'),
        schema='team_insight',
    )
    op.create_index('ix_team_insight_permissions_name', 'permissions', ['name'], unique=True, schema='team_insight')

    op.create_table(
        'role_permissions',
        sa.Column('role_id', sa.Integer(), sa.ForeignKey('team_insight.roles.id'), primary_key=True),
        sa.Column('permission_id', sa.Integer(), sa.ForeignKey('team_insight.permissions.id'), primary_key=True),
        schema='team_insight',
    )

    op.create_table(
        'user_roles',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('team_insight.users.id'), nullable=False),
        sa.Column('role_id', sa.Integer(), sa.ForeignKey('team_insight.roles.id'), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint('user_id', 'role_id', 'project_id', name='_user_role_project_uc'),
        schema='team_insight',
    )
