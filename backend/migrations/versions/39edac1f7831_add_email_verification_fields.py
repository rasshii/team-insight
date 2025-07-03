"""add_email_verification_fields

Revision ID: 39edac1f7831
Revises: 0b2776a53267
Create Date: 2025-06-26 13:47:58.754044

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '39edac1f7831'
down_revision: Union[str, None] = '0b2776a53267'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add email verification columns to users table
    op.add_column('users', sa.Column('is_email_verified', sa.Boolean(), nullable=False, server_default='false'), schema='team_insight')
    op.add_column('users', sa.Column('email_verification_token', sa.String(), nullable=True), schema='team_insight')
    op.add_column('users', sa.Column('email_verification_token_expires', sa.DateTime(), nullable=True), schema='team_insight')
    op.add_column('users', sa.Column('email_verified_at', sa.DateTime(), nullable=True), schema='team_insight')


def downgrade() -> None:
    # Remove email verification columns from users table
    op.drop_column('users', 'email_verified_at', schema='team_insight')
    op.drop_column('users', 'email_verification_token_expires', schema='team_insight')
    op.drop_column('users', 'email_verification_token', schema='team_insight')
    op.drop_column('users', 'is_email_verified', schema='team_insight')