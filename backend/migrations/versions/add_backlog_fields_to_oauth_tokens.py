"""Add Backlog specific fields to oauth_tokens

Revision ID: add_backlog_fields
Revises: 231fcecdce3a
Create Date: 2025-07-01 14:40:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'add_backlog_fields'
down_revision: Union[str, None] = '231fcecdce3a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add Backlog-specific columns to oauth_tokens table
    op.add_column('oauth_tokens', sa.Column('backlog_space_key', sa.String(length=100), nullable=True), schema='team_insight')
    op.add_column('oauth_tokens', sa.Column('backlog_user_id', sa.String(length=100), nullable=True), schema='team_insight')
    op.add_column('oauth_tokens', sa.Column('backlog_user_email', sa.String(length=255), nullable=True), schema='team_insight')
    op.add_column('oauth_tokens', sa.Column('last_used_at', sa.DateTime(), nullable=True), schema='team_insight')


def downgrade() -> None:
    # Remove Backlog-specific columns from oauth_tokens table
    op.drop_column('oauth_tokens', 'last_used_at', schema='team_insight')
    op.drop_column('oauth_tokens', 'backlog_user_email', schema='team_insight')
    op.drop_column('oauth_tokens', 'backlog_user_id', schema='team_insight')
    op.drop_column('oauth_tokens', 'backlog_space_key', schema='team_insight')