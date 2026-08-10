"""watch_party live co-view rooms.

Revision ID: f4a5b6c7d890
Revises: e3f4a5b6c7d8
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = 'f4a5b6c7d890'
down_revision: str | Sequence[str] | None = 'e3f4a5b6c7d8'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        'watch_party',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=False,
        ),
        sa.Column('invite_slug', sa.String(length=32), nullable=False),
        sa.Column('host_user_id', sa.Uuid(), nullable=False),
        sa.Column('film_id', sa.Integer(), nullable=False),
        sa.Column('playback_iframe_url', sa.String(length=2048), nullable=False),
        sa.Column('playback_expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('status', sa.String(length=16), server_default='active', nullable=False),
        sa.Column('max_members', sa.Integer(), nullable=True),
        sa.Column('playback_state', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('ended_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['film_id'], ['film.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['host_user_id'], ['user.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('invite_slug', name='uq_watch_party_invite_slug'),
    )
    op.create_index('ix_watch_party_invite_slug', 'watch_party', ['invite_slug'])
    op.create_index('ix_watch_party_host_user_id', 'watch_party', ['host_user_id'])
    op.create_index('ix_watch_party_film_id', 'watch_party', ['film_id'])
    op.create_index('ix_watch_party_status', 'watch_party', ['status'])

    op.create_table(
        'watch_party_member',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=False,
        ),
        sa.Column('party_id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('role', sa.String(length=8), nullable=False),
        sa.Column('status', sa.String(length=8), server_default='active', nullable=False),
        sa.Column(
            'last_seen_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=False,
        ),
        sa.Column(
            'joined_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(['party_id'], ['watch_party.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('party_id', 'user_id', name='uq_watch_party_member_party_user'),
    )
    op.create_index('ix_watch_party_member_party_id', 'watch_party_member', ['party_id'])
    op.create_index('ix_watch_party_member_user_id', 'watch_party_member', ['user_id'])
    op.create_index('ix_watch_party_member_status', 'watch_party_member', ['status'])
    op.create_index(
        'ix_watch_party_member_party_status',
        'watch_party_member',
        ['party_id', 'status'],
    )
    op.create_index(
        'ix_watch_party_member_user_status',
        'watch_party_member',
        ['user_id', 'status'],
    )

    op.create_table(
        'watch_party_message',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=False,
        ),
        sa.Column('party_id', sa.Uuid(), nullable=False),
        sa.Column('author_user_id', sa.Uuid(), nullable=False),
        sa.Column('body', sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(['author_user_id'], ['user.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['party_id'], ['watch_party.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_watch_party_message_party_id', 'watch_party_message', ['party_id'])
    op.create_index(
        'ix_watch_party_message_author_user_id',
        'watch_party_message',
        ['author_user_id'],
    )
    op.create_index(
        'ix_watch_party_message_party_id_id',
        'watch_party_message',
        ['party_id', 'id'],
    )


def downgrade() -> None:
    op.drop_index('ix_watch_party_message_party_id_id', table_name='watch_party_message')
    op.drop_index('ix_watch_party_message_author_user_id', table_name='watch_party_message')
    op.drop_index('ix_watch_party_message_party_id', table_name='watch_party_message')
    op.drop_table('watch_party_message')

    op.drop_index('ix_watch_party_member_user_status', table_name='watch_party_member')
    op.drop_index('ix_watch_party_member_party_status', table_name='watch_party_member')
    op.drop_index('ix_watch_party_member_status', table_name='watch_party_member')
    op.drop_index('ix_watch_party_member_user_id', table_name='watch_party_member')
    op.drop_index('ix_watch_party_member_party_id', table_name='watch_party_member')
    op.drop_table('watch_party_member')

    op.drop_index('ix_watch_party_status', table_name='watch_party')
    op.drop_index('ix_watch_party_film_id', table_name='watch_party')
    op.drop_index('ix_watch_party_host_user_id', table_name='watch_party')
    op.drop_index('ix_watch_party_invite_slug', table_name='watch_party')
    op.drop_table('watch_party')
