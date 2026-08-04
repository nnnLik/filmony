"""feed_post.body unlimited Text

Revision ID: l7m8n9o0p123
Revises: k6l7m8n9o012
Create Date: 2026-08-04

"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = 'l7m8n9o0p123'
down_revision: str | Sequence[str] | None = 'k6l7m8n9o012'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.alter_column(
        'feed_post',
        'body',
        existing_type=sa.String(length=2000),
        type_=sa.Text(),
        existing_nullable=False,
    )


def downgrade() -> None:
    op.alter_column(
        'feed_post',
        'body',
        existing_type=sa.Text(),
        type_=sa.String(length=2000),
        existing_nullable=False,
    )
