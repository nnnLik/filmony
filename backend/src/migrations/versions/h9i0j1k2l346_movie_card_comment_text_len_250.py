"""Restore movie_card_comment.text to 250 chars (align with API / validation).

Revision ID: h9i0j1k2l346
Revises: g8h9i0j1k234

33622715f72c_edit_len_comm shrunk this column to 100 on upgrade; backend and
frontend still enforce max length 250 (COMMENT_TEXT_MAX_LEN / COMMENT_BODY_MAX_LEN).
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = 'h9i0j1k2l346'
down_revision: str | Sequence[str] | None = 'g8h9i0j1k234'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.alter_column(
        'movie_card_comment',
        'text',
        existing_type=sa.String(length=100),
        type_=sa.String(length=250),
        existing_nullable=False,
    )


def downgrade() -> None:
    op.alter_column(
        'movie_card_comment',
        'text',
        existing_type=sa.String(length=250),
        type_=sa.String(length=100),
        existing_nullable=False,
        postgresql_using='left(text, 100)',
    )
