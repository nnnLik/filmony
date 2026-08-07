"""Add person and film_actor tables for Kinopoisk cast.

Revision ID: s4t5u6v7w890
Revises: r3s4t5u6v789
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = 's4t5u6v7w890'
down_revision: str | Sequence[str] | None = 'r3s4t5u6v789'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        'person',
        sa.Column('kinopoisk_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('poster_url', sa.String(length=2048), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=False,
        ),
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('kinopoisk_id', name='uq_person_kinopoisk_id'),
    )
    op.create_table(
        'film_actor',
        sa.Column('film_id', sa.Integer(), nullable=False),
        sa.Column('person_id', sa.Integer(), nullable=False),
        sa.Column('billing_order', sa.SmallInteger(), nullable=False),
        sa.Column('role', sa.String(length=512), nullable=True),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=False,
        ),
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.CheckConstraint(
            'billing_order >= 1 AND billing_order <= 10',
            name='ck_film_actor_billing_order_range',
        ),
        sa.ForeignKeyConstraint(['film_id'], ['film.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['person_id'], ['person.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('film_id', 'person_id', name='uq_film_actor_film_person'),
        sa.UniqueConstraint('film_id', 'billing_order', name='uq_film_actor_film_billing_order'),
    )
    op.create_index('ix_film_actor_film_id', 'film_actor', ['film_id'], unique=False)
    op.create_index('ix_film_actor_person_id', 'film_actor', ['person_id'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_film_actor_person_id', table_name='film_actor')
    op.drop_index('ix_film_actor_film_id', table_name='film_actor')
    op.drop_table('film_actor')
    op.drop_table('person')
