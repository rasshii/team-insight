"""Add sync_histories table only

Revision ID: add_sync_histories_manual
Revises: 39edac1f7831
Create Date: 2025-06-26 14:20:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'add_sync_histories_manual'
down_revision: Union[str, None] = '39edac1f7831'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create sync_histories table
    op.create_table('sync_histories',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('sync_type', sa.Enum('USER_TASKS', 'PROJECT_TASKS', 'ALL_PROJECTS', 'SINGLE_ISSUE', 'PROJECT_MEMBERS', name='synctype'), nullable=False),
    sa.Column('status', sa.Enum('STARTED', 'IN_PROGRESS', 'COMPLETED', 'FAILED', name='syncstatus'), nullable=False),
    sa.Column('target_id', sa.Integer(), nullable=True),
    sa.Column('target_name', sa.String(length=255), nullable=True),
    sa.Column('items_created', sa.Integer(), nullable=True),
    sa.Column('items_updated', sa.Integer(), nullable=True),
    sa.Column('items_failed', sa.Integer(), nullable=True),
    sa.Column('total_items', sa.Integer(), nullable=True),
    sa.Column('error_message', sa.Text(), nullable=True),
    sa.Column('error_details', sa.JSON(), nullable=True),
    sa.Column('started_at', sa.DateTime(), nullable=False),
    sa.Column('completed_at', sa.DateTime(), nullable=True),
    sa.Column('duration_seconds', sa.Integer(), nullable=True),
    sa.Column('sync_metadata', sa.JSON(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['team_insight.users.id'], ),
    sa.PrimaryKeyConstraint('id'),
    schema='team_insight'
    )
    op.create_index(op.f('ix_team_insight_sync_histories_id'), 'sync_histories', ['id'], unique=False, schema='team_insight')


def downgrade() -> None:
    # Drop sync_histories table
    op.drop_index(op.f('ix_team_insight_sync_histories_id'), table_name='sync_histories', schema='team_insight')
    op.drop_table('sync_histories', schema='team_insight')
    
    # Drop enum types
    op.execute("DROP TYPE IF EXISTS synctype")
    op.execute("DROP TYPE IF EXISTS syncstatus")