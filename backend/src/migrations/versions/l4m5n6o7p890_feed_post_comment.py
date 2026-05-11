"""feed_post_comment: comments on text feed posts.

Revision ID: l4m5n6o7p890
Revises: j2k3l4m5n678
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = 'l4m5n6o7p890'
down_revision: str | Sequence[str] | None = 'j2k3l4m5n678'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        'feed_post_comment',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('feed_post_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('parent_comment_id', sa.Integer(), nullable=True),
        sa.Column('text', sa.String(length=250), nullable=False),
        sa.ForeignKeyConstraint(['feed_post_id'], ['feed_post.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(
            ['parent_comment_id'], ['feed_post_comment.id'], ondelete='CASCADE'
        ),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(
        op.f('ix_feed_post_comment_feed_post_id'), 'feed_post_comment', ['feed_post_id']
    )
    op.create_index(
        op.f('ix_feed_post_comment_parent_comment_id'), 'feed_post_comment', ['parent_comment_id']
    )
    op.create_index(op.f('ix_feed_post_comment_user_id'), 'feed_post_comment', ['user_id'])
    op.create_index(
        'ix_feed_post_comment_post_parent_id',
        'feed_post_comment',
        ['feed_post_id', 'parent_comment_id', 'id'],
    )


def downgrade() -> None:
    op.drop_index('ix_feed_post_comment_post_parent_id', table_name='feed_post_comment')
    op.drop_index(op.f('ix_feed_post_comment_user_id'), table_name='feed_post_comment')
    op.drop_index(op.f('ix_feed_post_comment_parent_comment_id'), table_name='feed_post_comment')
    op.drop_index(op.f('ix_feed_post_comment_feed_post_id'), table_name='feed_post_comment')
    op.drop_table('feed_post_comment')
