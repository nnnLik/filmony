"""Add film_award_badge table for Oscar Best Picture badges.

Revision ID: q2r3s4t5u678
Revises: p1q2r3s4t567
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = 'q2r3s4t5u678'
down_revision: str | Sequence[str] | None = 'p1q2r3s4t567'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        'film_award_badge',
        sa.Column('film_id', sa.Integer(), nullable=False),
        sa.Column('kind', sa.String(length=32), nullable=False),
        sa.Column('ceremony_year', sa.Integer(), nullable=False),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=False,
        ),
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.ForeignKeyConstraint(['film_id'], ['film.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint(
            'film_id',
            'kind',
            'ceremony_year',
            name='uq_film_award_badge_film_kind_year',
        ),
    )
    op.create_index(
        op.f('ix_film_award_badge_film_id'),
        'film_award_badge',
        ['film_id'],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f('ix_film_award_badge_film_id'), table_name='film_award_badge')
    op.drop_table('film_award_badge')
