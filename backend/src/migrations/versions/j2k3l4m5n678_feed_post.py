"""feed_post: text posts for feed (optional image, card ref, source comment).

Revision ID: j2k3l4m5n678
Revises: i1j2k3l4m569
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = 'j2k3l4m5n678'
down_revision: str | Sequence[str] | None = 'i1j2k3l4m569'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        'feed_post',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('body', sa.String(length=2000), nullable=False),
        sa.Column('image_url', sa.String(length=2048), nullable=True),
        sa.Column('referenced_movie_card_id', sa.Integer(), nullable=True),
        sa.Column('source_comment_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(
            ['referenced_movie_card_id'], ['movie_card.id'], ondelete='SET NULL'
        ),
        sa.ForeignKeyConstraint(
            ['source_comment_id'], ['movie_card_comment.id'], ondelete='SET NULL'
        ),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(
        op.f('ix_feed_post_referenced_movie_card_id'), 'feed_post', ['referenced_movie_card_id']
    )
    op.create_index(op.f('ix_feed_post_source_comment_id'), 'feed_post', ['source_comment_id'])
    op.create_index(op.f('ix_feed_post_user_id'), 'feed_post', ['user_id'])
    op.create_index(
        'ix_feed_post_user_id_created_at_id',
        'feed_post',
        ['user_id', 'created_at', 'id'],
        postgresql_ops={'created_at': 'DESC', 'id': 'DESC'},
    )


def downgrade() -> None:
    op.drop_index('ix_feed_post_user_id_created_at_id', table_name='feed_post')
    op.drop_index(op.f('ix_feed_post_user_id'), table_name='feed_post')
    op.drop_index(op.f('ix_feed_post_source_comment_id'), table_name='feed_post')
    op.drop_index(op.f('ix_feed_post_referenced_movie_card_id'), table_name='feed_post')
    op.drop_table('feed_post')
