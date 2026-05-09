"""reaction_type: drop label, sort_order, is_active; require category_slug and asset_key

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-05-10

"""

from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa
from alembic import op

revision: str = 'b2c3d4e5f6a7'
down_revision: str | Sequence[str] | None = 'a1b2c3d4e5f6'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        sa.text(
            "UPDATE reaction_type SET category_slug = 'misc' "
            "WHERE category_slug IS NULL OR btrim(category_slug) = ''"
        )
    )
    op.execute(
        sa.text(
            'UPDATE reaction_type SET asset_key = image_url '
            "WHERE asset_key IS NULL OR btrim(asset_key) = ''"
        )
    )
    op.drop_index(op.f('ix_reaction_type_sort_order'), table_name='reaction_type')
    op.drop_column('reaction_type', 'label')
    op.drop_column('reaction_type', 'sort_order')
    op.drop_column('reaction_type', 'is_active')
    op.alter_column(
        'reaction_type',
        'category_slug',
        existing_type=sa.String(length=120),
        nullable=False,
    )
    op.alter_column(
        'reaction_type',
        'asset_key',
        existing_type=sa.String(length=512),
        nullable=False,
    )


def downgrade() -> None:
    op.alter_column(
        'reaction_type',
        'asset_key',
        existing_type=sa.String(length=512),
        nullable=True,
    )
    op.alter_column(
        'reaction_type',
        'category_slug',
        existing_type=sa.String(length=120),
        nullable=True,
    )
    op.add_column(
        'reaction_type',
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
    )
    op.add_column(
        'reaction_type',
        sa.Column('sort_order', sa.Integer(), nullable=False, server_default=sa.text('0')),
    )
    op.add_column(
        'reaction_type',
        sa.Column('label', sa.String(length=120), nullable=True),
    )
    op.create_index(
        op.f('ix_reaction_type_sort_order'),
        'reaction_type',
        ['sort_order'],
        unique=False,
    )
    op.execute(sa.text('UPDATE reaction_type SET is_active = true'))
    op.alter_column('reaction_type', 'is_active', server_default=None)
