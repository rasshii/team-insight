"""remove password related columns

Revision ID: remove_password_columns
Revises: add_report_schedule_tables
Create Date: 2025-07-02 13:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'remove_password_columns'
down_revision = 'add_report_schedule_tables'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Remove password and email verification related columns as we're using Backlog OAuth only
    """
    # Drop columns from users table
    op.drop_column('users', 'hashed_password', schema='team_insight')
    op.drop_column('users', 'is_email_verified', schema='team_insight')
    op.drop_column('users', 'email_verification_token', schema='team_insight')
    op.drop_column('users', 'email_verification_token_expires', schema='team_insight')
    op.drop_column('users', 'email_verified_at', schema='team_insight')


def downgrade() -> None:
    """
    Re-add password and email verification columns
    """
    # Re-add columns to users table
    op.add_column('users', sa.Column('hashed_password', sa.String(), nullable=True), schema='team_insight')
    op.add_column('users', sa.Column('is_email_verified', sa.Boolean(), nullable=False, server_default='false'), schema='team_insight')
    op.add_column('users', sa.Column('email_verification_token', sa.String(), nullable=True), schema='team_insight')
    op.add_column('users', sa.Column('email_verification_token_expires', sa.DateTime(), nullable=True), schema='team_insight')
    op.add_column('users', sa.Column('email_verified_at', sa.DateTime(), nullable=True), schema='team_insight')