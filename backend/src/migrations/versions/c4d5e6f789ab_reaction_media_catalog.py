"""reaction media keys, categories, user recent reactions

Revision ID: c4d5e6f789ab
Revises: 17e05799f842
Create Date: 2026-05-07

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = 'c4d5e6f789ab'
down_revision: str | Sequence[str] | None = '17e05799f842'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        'reaction_type',
        sa.Column('category_slug', sa.String(length=120), nullable=True),
    )
    op.add_column(
        'reaction_type',
        sa.Column('asset_key', sa.String(length=512), nullable=True),
    )
    op.create_index(
        op.f('ix_reaction_type_category_slug'),
        'reaction_type',
        ['category_slug'],
        unique=False,
    )
    op.create_unique_constraint('uq_reaction_type_asset_key', 'reaction_type', ['asset_key'])

    op.create_table(
        'user_recent_reaction',
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('reaction_type_id', sa.Integer(), nullable=False),
        sa.Column(
            'last_used_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(['reaction_type_id'], ['reaction_type.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint(
            'user_id',
            'reaction_type_id',
            name='uq_user_recent_reaction_user_rt',
        ),
    )
    op.create_index(
        op.f('ix_user_recent_reaction_user_id'),
        'user_recent_reaction',
        ['user_id'],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f('ix_user_recent_reaction_user_id'), table_name='user_recent_reaction')
    op.drop_table('user_recent_reaction')
    op.drop_constraint('uq_reaction_type_asset_key', 'reaction_type', type_='unique')
    op.drop_index(op.f('ix_reaction_type_category_slug'), table_name='reaction_type')
    op.drop_column('reaction_type', 'asset_key')
    op.drop_column('reaction_type', 'category_slug')
