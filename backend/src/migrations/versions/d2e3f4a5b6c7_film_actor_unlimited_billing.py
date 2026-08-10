"""Allow unlimited film_actor billing_order (>= 1).

Revision ID: d2e3f4a5b6c7
Revises: t5u6v7w8x901
"""

from collections.abc import Sequence

from alembic import op

revision: str = 'd2e3f4a5b6c7'
down_revision: str | Sequence[str] | None = 't5u6v7w8x901'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_constraint('ck_film_actor_billing_order_range', 'film_actor', type_='check')
    op.create_check_constraint(
        'ck_film_actor_billing_order_range',
        'film_actor',
        'billing_order >= 1',
    )


def downgrade() -> None:
    op.drop_constraint('ck_film_actor_billing_order_range', 'film_actor', type_='check')
    op.create_check_constraint(
        'ck_film_actor_billing_order_range',
        'film_actor',
        'billing_order >= 1 AND billing_order <= 10',
    )
