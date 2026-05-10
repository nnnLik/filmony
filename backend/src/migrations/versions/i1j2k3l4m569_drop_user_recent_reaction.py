"""Drop user_recent_reaction (recent picks stored on client).

Revision ID: i1j2k3l4m569
Revises: h9i0j1k2l346
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = 'i1j2k3l4m569'
down_revision: str | Sequence[str] | None = 'h9i0j1k2l346'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_index(op.f('ix_user_recent_reaction_user_id'), table_name='user_recent_reaction')
    op.drop_table('user_recent_reaction')


def downgrade() -> None:
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
