"""partial unique index for youtube user_card external subjects

Revision ID: a2b3c4d5e678
Revises: z1a2b3c4d567
Create Date: 2026-07-19

"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = 'a2b3c4d5e678'
down_revision: str | Sequence[str] | None = 'z1a2b3c4d567'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_index(
        'uq_user_card_user_provider_external_youtube_partial',
        'user_card',
        ['user_id', 'provider', 'external_id'],
        unique=True,
        postgresql_where=sa.text("provider = 'youtube' AND external_id IS NOT NULL"),
    )


def downgrade() -> None:
    op.drop_index(
        'uq_user_card_user_provider_external_youtube_partial',
        table_name='user_card',
    )
