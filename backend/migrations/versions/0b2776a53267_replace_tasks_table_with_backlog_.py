"""Replace tasks table with Backlog-integrated version

Revision ID: 0b2776a53267
Revises: faba2f3bfca7
Create Date: 2025-06-25 23:53:16.611335

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0b2776a53267'
down_revision: Union[str, None] = 'faba2f3bfca7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Drop the old tasks table
    op.drop_table('tasks', schema='team_insight')
    
    # Create the new tasks table with Backlog integration
    op.create_table('tasks',
    sa.Column('backlog_id', sa.Integer(), nullable=False),
    sa.Column('backlog_key', sa.String(length=255), nullable=False),
    sa.Column('project_id', sa.Integer(), nullable=True),
    sa.Column('assignee_id', sa.Integer(), nullable=True),
    sa.Column('reporter_id', sa.Integer(), nullable=True),
    sa.Column('title', sa.String(length=255), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('status', sa.Enum('TODO', 'IN_PROGRESS', 'RESOLVED', 'CLOSED', name='taskstatus'), nullable=False),
    sa.Column('priority', sa.Integer(), nullable=True),
    sa.Column('issue_type_id', sa.Integer(), nullable=True),
    sa.Column('issue_type_name', sa.String(length=100), nullable=True),
    sa.Column('estimated_hours', sa.Float(), nullable=True),
    sa.Column('actual_hours', sa.Float(), nullable=True),
    sa.Column('start_date', sa.DateTime(), nullable=True),
    sa.Column('due_date', sa.DateTime(), nullable=True),
    sa.Column('completed_date', sa.DateTime(), nullable=True),
    sa.Column('milestone_id', sa.Integer(), nullable=True),
    sa.Column('milestone_name', sa.String(length=255), nullable=True),
    sa.Column('category_names', sa.Text(), nullable=True),
    sa.Column('version_names', sa.Text(), nullable=True),
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['assignee_id'], ['team_insight.users.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['project_id'], ['team_insight.projects.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['reporter_id'], ['team_insight.users.id'], ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('backlog_key'),
    schema='team_insight'
    )
    op.create_index(op.f('ix_team_insight_tasks_backlog_id'), 'tasks', ['backlog_id'], unique=True, schema='team_insight')
    op.create_index(op.f('ix_team_insight_tasks_id'), 'tasks', ['id'], unique=False, schema='team_insight')


def downgrade() -> None:
    # Drop the new tasks table
    op.drop_index(op.f('ix_team_insight_tasks_id'), table_name='tasks', schema='team_insight')
    op.drop_index(op.f('ix_team_insight_tasks_backlog_id'), table_name='tasks', schema='team_insight')
    op.drop_table('tasks', schema='team_insight')
    
    # Recreate the old tasks table
    op.create_table('tasks',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('title', sa.String(length=255), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('project_id', sa.Integer(), nullable=True),
    sa.Column('assigned_to', sa.Integer(), nullable=True),
    sa.Column('status', sa.String(length=50), nullable=False),
    sa.Column('priority', sa.String(length=50), nullable=False),
    sa.Column('due_date', sa.DateTime(timezone=True), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=True, server_default=sa.text('CURRENT_TIMESTAMP')),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True, server_default=sa.text('CURRENT_TIMESTAMP')),
    sa.PrimaryKeyConstraint('id'),
    schema='team_insight'
    )
    op.create_index('idx_tasks_assigned_to', 'tasks', ['assigned_to'], unique=False, schema='team_insight')
    op.create_index('idx_tasks_project_id', 'tasks', ['project_id'], unique=False, schema='team_insight')
