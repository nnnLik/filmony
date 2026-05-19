"""Ensure catalog_item.created_at exists (idempotent).

Older or partially upgraded databases may lack ``catalog_item.created_at`` while
``CatalogItem`` inherits ``CreatedAtMixin``. ``bd8f039d04fe_card`` already adds this
column for normal upgrade chains; this revision is a no-op when the column is present.

Revision ID: k7l8m9n0o123
Revises: bd8f039d04fe
Create Date: 2026-05-15

"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = 'k7l8m9n0o123'
down_revision: str | Sequence[str] | None = 'bd8f039d04fe'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    conn = op.get_bind()
    insp = sa.inspect(conn)
    if 'catalog_item' not in insp.get_table_names():
        return
    cols = {c['name'] for c in insp.get_columns('catalog_item')}
    if 'created_at' in cols:
        return
    op.add_column(
        'catalog_item',
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    )


def downgrade() -> None:
    """No-op: ``bd8f039d04fe`` owns add/drop of this column on full downgrades."""
    pass
