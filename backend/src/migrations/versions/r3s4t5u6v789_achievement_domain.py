"""Add achievement catalog, user unlocks, and profile pins.

Revision ID: r3s4t5u6v789
Revises: q2r3s4t5u678
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = 'r3s4t5u6v789'
down_revision: str | Sequence[str] | None = 'q2r3s4t5u678'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        'achievement',
        sa.Column('slug', sa.String(length=64), nullable=False),
        sa.Column('collection_slug', sa.String(length=64), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('icon_key', sa.String(length=64), nullable=True),
        sa.Column('holders_count', sa.Integer(), server_default='0', nullable=False),
        sa.Column('eligible_users_count', sa.Integer(), server_default='0', nullable=False),
        sa.Column('rarity_percent', sa.Numeric(precision=8, scale=4), nullable=True),
        sa.Column('rarity_calculated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=False,
        ),
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('collection_slug', name='uq_achievement_collection_slug'),
        sa.UniqueConstraint('slug', name='uq_achievement_slug'),
    )
    op.create_index(
        'ix_achievement_collection_slug', 'achievement', ['collection_slug'], unique=False
    )
    op.create_index('ix_achievement_slug', 'achievement', ['slug'], unique=False)

    op.create_table(
        'user_achievement',
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('achievement_id', sa.Integer(), nullable=False),
        sa.Column(
            'unlocked_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=False,
        ),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=False,
        ),
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.ForeignKeyConstraint(['achievement_id'], ['achievement.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint(
            'user_id',
            'achievement_id',
            name='uq_user_achievement_user_achievement',
        ),
    )
    op.create_index('ix_user_achievement_user_id', 'user_achievement', ['user_id'], unique=False)

    op.create_table(
        'user_achievement_pin',
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('achievement_id', sa.Integer(), nullable=False),
        sa.Column('slot_index', sa.SmallInteger(), nullable=False),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=False,
        ),
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.ForeignKeyConstraint(['achievement_id'], ['achievement.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint(
            'user_id',
            'achievement_id',
            name='uq_user_achievement_pin_user_achievement',
        ),
        sa.UniqueConstraint(
            'user_id',
            'slot_index',
            name='uq_user_achievement_pin_user_slot',
        ),
    )
    op.create_index(
        'ix_user_achievement_pin_user_id', 'user_achievement_pin', ['user_id'], unique=False
    )


def downgrade() -> None:
    op.drop_index('ix_user_achievement_pin_user_id', table_name='user_achievement_pin')
    op.drop_table('user_achievement_pin')
    op.drop_index('ix_user_achievement_user_id', table_name='user_achievement')
    op.drop_table('user_achievement')
    op.drop_index('ix_achievement_slug', table_name='achievement')
    op.drop_index('ix_achievement_collection_slug', table_name='achievement')
    op.drop_table('achievement')
