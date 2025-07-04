"""Add status_id field to tasks table

Revision ID: 23220042b64e
Revises: 8f49f3333b0b
Create Date: 2025-07-02 17:59:39.116932

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '23220042b64e'
down_revision: Union[str, None] = '8f49f3333b0b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('tasks', sa.Column('status_id', sa.Integer(), nullable=True), schema='team_insight')
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('tasks', 'status_id', schema='team_insight')
    # ### end Alembic commands ###