"""Add teams and team_members tables

Revision ID: 8f49f3333b0b
Revises: 881655b2d54f
Create Date: 2025-07-02 16:28:43.161354

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '8f49f3333b0b'
down_revision: Union[str, None] = '881655b2d54f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create teams table
    op.create_table('teams',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=100), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name'),
    schema='team_insight'
    )
    op.create_index(op.f('ix_team_insight_teams_id'), 'teams', ['id'], unique=False, schema='team_insight')
    op.create_index(op.f('ix_team_insight_teams_name'), 'teams', ['name'], unique=False, schema='team_insight')
    
    # Create team_members table (using String instead of Enum for role)
    op.create_table('team_members',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('team_id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('role', sa.String(length=50), nullable=False),
    sa.Column('joined_at', sa.DateTime(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['team_id'], ['team_insight.teams.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['team_insight.users.id'], ),
    sa.PrimaryKeyConstraint('id'),
    schema='team_insight'
    )
    op.create_index(op.f('ix_team_insight_team_members_id'), 'team_members', ['id'], unique=False, schema='team_insight')
    
    # Add unique constraint to prevent duplicate team memberships
    op.create_unique_constraint('uq_team_members_team_user', 'team_members', ['team_id', 'user_id'], schema='team_insight')


def downgrade() -> None:
    # Drop team_members table and constraint
    op.drop_constraint('uq_team_members_team_user', 'team_members', schema='team_insight')
    op.drop_index(op.f('ix_team_insight_team_members_id'), table_name='team_members', schema='team_insight')
    op.drop_table('team_members', schema='team_insight')
    
    # Drop teams table
    op.drop_index(op.f('ix_team_insight_teams_name'), table_name='teams', schema='team_insight')
    op.drop_index(op.f('ix_team_insight_teams_id'), table_name='teams', schema='team_insight')
    op.drop_table('teams', schema='team_insight')
