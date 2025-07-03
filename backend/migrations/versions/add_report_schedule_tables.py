"""add report schedule tables

Revision ID: add_report_schedule_tables
Revises: add_backlog_fields
Create Date: 2025-07-02 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_report_schedule_tables'
down_revision = 'add_backlog_fields'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create report_schedules table
    op.create_table('report_schedules',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('report_type', sa.String(), nullable=False),
        sa.Column('recipient_type', sa.String(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=True),
        sa.Column('enabled', sa.Boolean(), nullable=False, default=True),
        sa.Column('send_time', sa.Time(), nullable=True),
        sa.Column('last_sent_at', sa.DateTime(), nullable=True),
        sa.Column('next_send_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['team_insight.users.id'], ),
        sa.ForeignKeyConstraint(['project_id'], ['team_insight.projects.id'], ),
        sa.PrimaryKeyConstraint('id'),
        schema='team_insight'
    )
    op.create_index(op.f('ix_team_insight_report_schedules_id'), 'report_schedules', ['id'], unique=False, schema='team_insight')
    
    # Create report_delivery_history table
    op.create_table('report_delivery_history',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('schedule_id', sa.Integer(), nullable=True),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('report_type', sa.String(), nullable=False),
        sa.Column('recipient_type', sa.String(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=True),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('error_message', sa.String(), nullable=True),
        sa.Column('sent_at', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['schedule_id'], ['team_insight.report_schedules.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['team_insight.users.id'], ),
        sa.ForeignKeyConstraint(['project_id'], ['team_insight.projects.id'], ),
        sa.PrimaryKeyConstraint('id'),
        schema='team_insight'
    )
    op.create_index(op.f('ix_team_insight_report_delivery_history_id'), 'report_delivery_history', ['id'], unique=False, schema='team_insight')


def downgrade() -> None:
    op.drop_index(op.f('ix_team_insight_report_delivery_history_id'), table_name='report_delivery_history', schema='team_insight')
    op.drop_table('report_delivery_history', schema='team_insight')
    op.drop_index(op.f('ix_team_insight_report_schedules_id'), table_name='report_schedules', schema='team_insight')
    op.drop_table('report_schedules', schema='team_insight')