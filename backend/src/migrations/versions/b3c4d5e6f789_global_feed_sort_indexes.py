"""Global feed sort indexes on user_card.updated_at and feed_post.created_at.

Revision ID: b3c4d5e6f789
Revises: a2b3c4d5e678
"""

from collections.abc import Sequence

from alembic import op

revision: str = 'b3c4d5e6f789'
down_revision: str | Sequence[str] | None = 'a2b3c4d5e678'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_index(
        'ix_user_card_updated_at_id',
        'user_card',
        ['updated_at', 'id'],
        unique=False,
        postgresql_ops={'updated_at': 'DESC', 'id': 'DESC'},
    )
    op.create_index(
        'ix_feed_post_created_at_id',
        'feed_post',
        ['created_at', 'id'],
        unique=False,
        postgresql_ops={'created_at': 'DESC', 'id': 'DESC'},
    )


def downgrade() -> None:
    op.drop_index('ix_feed_post_created_at_id', table_name='feed_post')
    op.drop_index('ix_user_card_updated_at_id', table_name='user_card')
