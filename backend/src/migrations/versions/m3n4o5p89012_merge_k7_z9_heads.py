"""Merge migration: reconcile parallel heads from catalog_item and user_reaction index work.

Revision ID: m3n4o5p89012
Revises: k7l8m9n0o123, z9y8x7w65431
Create Date: 2026-05-14

"""

from __future__ import annotations

from collections.abc import Sequence

revision: str = 'm3n4o5p89012'
down_revision: str | Sequence[str] | None = ('k7l8m9n0o123', 'z9y8x7w65431')
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
