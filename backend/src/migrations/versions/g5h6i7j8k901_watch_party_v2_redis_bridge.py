"""drop watch_party_message; add watch_party_watch_session_link

Revision ID: g5h6i7j8k901
Revises: f4a5b6c7d890

Avoid ALTER TABLE watch_session — prod app role may not own that legacy table.
Traceability uses a new link table with FK references instead.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = 'g5h6i7j8k901'
down_revision: str | Sequence[str] | None = 'f4a5b6c7d890'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_index('ix_watch_party_message_party_id_id', table_name='watch_party_message')
    op.drop_index('ix_watch_party_message_author_user_id', table_name='watch_party_message')
    op.drop_index('ix_watch_party_message_party_id', table_name='watch_party_message')
    op.drop_table('watch_party_message')

    op.create_table(
        'watch_party_watch_session_link',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('watch_session_id', sa.Uuid(), nullable=False),
        sa.Column('watch_party_id', sa.Uuid(), nullable=False),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ['watch_session_id'],
            ['watch_session.id'],
            ondelete='CASCADE',
        ),
        sa.ForeignKeyConstraint(
            ['watch_party_id'],
            ['watch_party.id'],
            ondelete='CASCADE',
        ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint(
            'watch_session_id',
            name='uq_watch_party_watch_session_link_session',
        ),
    )
    op.create_index(
        'ix_watch_party_watch_session_link_party_id',
        'watch_party_watch_session_link',
        ['watch_party_id'],
    )


def downgrade() -> None:
    op.drop_index(
        'ix_watch_party_watch_session_link_party_id',
        table_name='watch_party_watch_session_link',
    )
    op.drop_table('watch_party_watch_session_link')

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
