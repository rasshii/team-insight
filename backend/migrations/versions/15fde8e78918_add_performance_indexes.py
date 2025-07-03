"""add_performance_indexes

Revision ID: 15fde8e78918
Revises: add_sync_histories_manual
Create Date: 2025-06-26 23:58:54.910086

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '15fde8e78918'
down_revision: Union[str, None] = 'add_sync_histories_manual'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
