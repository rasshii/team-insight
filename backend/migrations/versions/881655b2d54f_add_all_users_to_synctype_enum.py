"""Add ALL_USERS to SyncType enum

Revision ID: 881655b2d54f
Revises: remove_password_columns
Create Date: 2025-07-02 16:00:00.836279

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '881655b2d54f'
down_revision: Union[str, None] = 'remove_password_columns'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # PostgreSQLのENUM型に新しい値を追加
    op.execute("ALTER TYPE synctype ADD VALUE IF NOT EXISTS 'ALL_USERS'")


def downgrade() -> None:
    # PostgreSQLではENUM型から値を削除することはできないため、
    # ダウングレードは実装しない（コメントで警告）
    pass  # Cannot remove values from ENUM type in PostgreSQL
