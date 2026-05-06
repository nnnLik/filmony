"""enchant-user — поля публичного профиля

Revision ID: 110da8652616
Revises: ac3f8989b766
Create Date: 2026-05-06 00:10:49.897657

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = '110da8652616'
down_revision: str | Sequence[str] | None = 'ac3f8989b766'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column('user', sa.Column('profile_slug', sa.String(length=32), nullable=True))
    op.add_column('user', sa.Column('display_name', sa.String(length=120), nullable=True))
    op.add_column('user', sa.Column('bio', sa.String(length=500), nullable=True))
    op.execute(
        sa.text(
            """
            UPDATE "user"
            SET profile_slug = 'u' || substring(replace(cast(id as text), '-', '') from 1 for 12)
            WHERE profile_slug IS NULL
            """
        )
    )
    op.alter_column('user', 'profile_slug', nullable=False)
    op.create_index(op.f('ix_user_profile_slug'), 'user', ['profile_slug'], unique=True)


def downgrade() -> None:
    op.drop_index(op.f('ix_user_profile_slug'), table_name='user')
    op.drop_column('user', 'bio')
    op.drop_column('user', 'display_name')
    op.drop_column('user', 'profile_slug')
