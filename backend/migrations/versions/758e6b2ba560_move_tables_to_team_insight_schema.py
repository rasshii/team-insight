"""move tables to team_insight schema

Revision ID: 758e6b2ba560
Revises: 5333a4ae1265
Create Date: 2025-06-16 16:56:14.422179

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '758e6b2ba560'
down_revision: Union[str, None] = '5333a4ae1265'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('users',
    sa.Column('email', sa.String(), nullable=True),
    sa.Column('hashed_password', sa.String(), nullable=True),
    sa.Column('full_name', sa.String(), nullable=True),
    sa.Column('is_active', sa.Boolean(), nullable=True),
    sa.Column('is_superuser', sa.Boolean(), nullable=True),
    sa.Column('backlog_id', sa.Integer(), nullable=True),
    sa.Column('user_id', sa.String(), nullable=True),
    sa.Column('name', sa.String(), nullable=True),
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    schema='team_insight'
    )
    op.create_index(op.f('ix_team_insight_users_backlog_id'), 'users', ['backlog_id'], unique=True, schema='team_insight')
    op.create_index(op.f('ix_team_insight_users_email'), 'users', ['email'], unique=True, schema='team_insight')
    op.create_index(op.f('ix_team_insight_users_id'), 'users', ['id'], unique=False, schema='team_insight')
    op.create_index(op.f('ix_team_insight_users_user_id'), 'users', ['user_id'], unique=True, schema='team_insight')
    op.create_table('oauth_states',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('state', sa.String(length=255), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('expires_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['team_insight.users.id'], ),
    sa.PrimaryKeyConstraint('id'),
    schema='team_insight'
    )
    op.create_index(op.f('ix_team_insight_oauth_states_id'), 'oauth_states', ['id'], unique=False, schema='team_insight')
    op.create_index(op.f('ix_team_insight_oauth_states_state'), 'oauth_states', ['state'], unique=True, schema='team_insight')
    op.create_table('oauth_tokens',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('provider', sa.String(length=50), nullable=False),
    sa.Column('access_token', sa.Text(), nullable=False),
    sa.Column('refresh_token', sa.Text(), nullable=True),
    sa.Column('expires_at', sa.DateTime(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['team_insight.users.id'], ),
    sa.PrimaryKeyConstraint('id'),
    schema='team_insight'
    )
    op.create_index(op.f('ix_team_insight_oauth_tokens_id'), 'oauth_tokens', ['id'], unique=False, schema='team_insight')
    op.drop_index('ix_oauth_tokens_id', table_name='oauth_tokens')
    op.drop_table('oauth_tokens')
    op.drop_index('ix_oauth_states_id', table_name='oauth_states')
    op.drop_index('ix_oauth_states_state', table_name='oauth_states')
    op.drop_table('oauth_states')
    op.drop_index('ix_users_backlog_id', table_name='users')
    op.drop_index('ix_users_email', table_name='users')
    op.drop_index('ix_users_id', table_name='users')
    op.drop_index('ix_users_user_id', table_name='users')
    op.drop_table('users')
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('users',
    sa.Column('email', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('hashed_password', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('full_name', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('is_active', sa.BOOLEAN(), autoincrement=False, nullable=True),
    sa.Column('is_superuser', sa.BOOLEAN(), autoincrement=False, nullable=True),
    sa.Column('backlog_id', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('user_id', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('name', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('id', sa.INTEGER(), server_default=sa.text("nextval('users_id_seq'::regclass)"), autoincrement=True, nullable=False),
    sa.Column('created_at', postgresql.TIMESTAMP(), autoincrement=False, nullable=True),
    sa.Column('updated_at', postgresql.TIMESTAMP(), autoincrement=False, nullable=True),
    sa.PrimaryKeyConstraint('id', name='users_pkey'),
    postgresql_ignore_search_path=False
    )
    op.create_index('ix_users_user_id', 'users', ['user_id'], unique=True)
    op.create_index('ix_users_id', 'users', ['id'], unique=False)
    op.create_index('ix_users_email', 'users', ['email'], unique=True)
    op.create_index('ix_users_backlog_id', 'users', ['backlog_id'], unique=True)
    op.create_table('oauth_states',
    sa.Column('id', sa.INTEGER(), autoincrement=True, nullable=False),
    sa.Column('state', sa.VARCHAR(length=255), autoincrement=False, nullable=False),
    sa.Column('user_id', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('created_at', postgresql.TIMESTAMP(), autoincrement=False, nullable=True),
    sa.Column('expires_at', postgresql.TIMESTAMP(), autoincrement=False, nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name='oauth_states_user_id_fkey'),
    sa.PrimaryKeyConstraint('id', name='oauth_states_pkey')
    )
    op.create_index('ix_oauth_states_state', 'oauth_states', ['state'], unique=True)
    op.create_index('ix_oauth_states_id', 'oauth_states', ['id'], unique=False)
    op.create_table('oauth_tokens',
    sa.Column('id', sa.INTEGER(), autoincrement=True, nullable=False),
    sa.Column('user_id', sa.INTEGER(), autoincrement=False, nullable=False),
    sa.Column('provider', sa.VARCHAR(length=50), autoincrement=False, nullable=False),
    sa.Column('access_token', sa.TEXT(), autoincrement=False, nullable=False),
    sa.Column('refresh_token', sa.TEXT(), autoincrement=False, nullable=True),
    sa.Column('expires_at', postgresql.TIMESTAMP(), autoincrement=False, nullable=True),
    sa.Column('created_at', postgresql.TIMESTAMP(), autoincrement=False, nullable=True),
    sa.Column('updated_at', postgresql.TIMESTAMP(), autoincrement=False, nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name='oauth_tokens_user_id_fkey'),
    sa.PrimaryKeyConstraint('id', name='oauth_tokens_pkey')
    )
    op.create_index('ix_oauth_tokens_id', 'oauth_tokens', ['id'], unique=False)
    op.drop_index(op.f('ix_team_insight_oauth_tokens_id'), table_name='oauth_tokens', schema='team_insight')
    op.drop_table('oauth_tokens', schema='team_insight')
    op.drop_index(op.f('ix_team_insight_oauth_states_state'), table_name='oauth_states', schema='team_insight')
    op.drop_index(op.f('ix_team_insight_oauth_states_id'), table_name='oauth_states', schema='team_insight')
    op.drop_table('oauth_states', schema='team_insight')
    op.drop_index(op.f('ix_team_insight_users_user_id'), table_name='users', schema='team_insight')
    op.drop_index(op.f('ix_team_insight_users_id'), table_name='users', schema='team_insight')
    op.drop_index(op.f('ix_team_insight_users_email'), table_name='users', schema='team_insight')
    op.drop_index(op.f('ix_team_insight_users_backlog_id'), table_name='users', schema='team_insight')
    op.drop_table('users', schema='team_insight')
    # ### end Alembic commands ###
