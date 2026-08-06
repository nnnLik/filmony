"""Add collection domain tables for curated film lists and user progress.

Revision ID: p1q2r3s4t567
Revises: o7p8q9r0s123
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = 'p1q2r3s4t567'
down_revision: str | Sequence[str] | None = 'o7p8q9r0s123'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        'collection',
        sa.Column('slug', sa.String(length=64), nullable=False),
        sa.Column('kind', sa.String(length=16), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('season_year', sa.Integer(), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default=sa.text('true'), nullable=False),
        sa.Column('film_count', sa.Integer(), server_default='0', nullable=False),
        sa.Column(
            'content_updated_at',
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
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('slug'),
    )
    op.create_index(op.f('ix_collection_slug'), 'collection', ['slug'], unique=True)

    op.create_table(
        'collection_film',
        sa.Column('collection_id', sa.Integer(), nullable=False),
        sa.Column('film_id', sa.Integer(), nullable=False),
        sa.Column('sort_order', sa.Integer(), server_default='0', nullable=False),
        sa.Column('seed_imdb_id', sa.String(length=16), nullable=True),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=False,
        ),
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.ForeignKeyConstraint(
            ['collection_id'],
            ['collection.id'],
            name=op.f('fk_collection_film_collection_id_collection'),
            ondelete='CASCADE',
        ),
        sa.ForeignKeyConstraint(
            ['film_id'],
            ['film.id'],
            name=op.f('fk_collection_film_film_id_film'),
            ondelete='CASCADE',
        ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint(
            'collection_id',
            'film_id',
            name='uq_collection_film_collection_film',
        ),
    )
    op.create_index(
        'ix_collection_film_collection_id_sort_order',
        'collection_film',
        ['collection_id', 'sort_order'],
        unique=False,
    )

    op.create_table(
        'user_collection_progress',
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('collection_id', sa.Integer(), nullable=False),
        sa.Column('rated_count', sa.Integer(), server_default='0', nullable=False),
        sa.Column('total_count', sa.Integer(), server_default='0', nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=False,
        ),
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.ForeignKeyConstraint(
            ['collection_id'],
            ['collection.id'],
            name=op.f('fk_user_collection_progress_collection_id_collection'),
            ondelete='CASCADE',
        ),
        sa.ForeignKeyConstraint(
            ['user_id'],
            ['user.id'],
            name=op.f('fk_user_collection_progress_user_id_user'),
            ondelete='CASCADE',
        ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint(
            'user_id',
            'collection_id',
            name='uq_user_collection_progress_user_collection',
        ),
    )
    op.create_index(
        op.f('ix_user_collection_progress_user_id'),
        'user_collection_progress',
        ['user_id'],
        unique=False,
    )

    op.create_table(
        'user_collection_pin',
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('collection_id', sa.Integer(), nullable=False),
        sa.Column('sort_order', sa.Integer(), server_default='0', nullable=False),
        sa.Column(
            'pinned_at',
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
        sa.ForeignKeyConstraint(
            ['collection_id'],
            ['collection.id'],
            name=op.f('fk_user_collection_pin_collection_id_collection'),
            ondelete='CASCADE',
        ),
        sa.ForeignKeyConstraint(
            ['user_id'],
            ['user.id'],
            name=op.f('fk_user_collection_pin_user_id_user'),
            ondelete='CASCADE',
        ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint(
            'user_id',
            'collection_id',
            name='uq_user_collection_pin_user_collection',
        ),
    )
    op.create_index(
        op.f('ix_user_collection_pin_user_id'),
        'user_collection_pin',
        ['user_id'],
        unique=False,
    )
    op.create_index(
        'ix_user_collection_pin_user_id_sort_order',
        'user_collection_pin',
        ['user_id', 'sort_order'],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index('ix_user_collection_pin_user_id_sort_order', table_name='user_collection_pin')
    op.drop_index(op.f('ix_user_collection_pin_user_id'), table_name='user_collection_pin')
    op.drop_table('user_collection_pin')
    op.drop_index(
        op.f('ix_user_collection_progress_user_id'),
        table_name='user_collection_progress',
    )
    op.drop_table('user_collection_progress')
    op.drop_index('ix_collection_film_collection_id_sort_order', table_name='collection_film')
    op.drop_table('collection_film')
    op.drop_index(op.f('ix_collection_slug'), table_name='collection')
    op.drop_table('collection')
