"""reactions catalog and user reactions

Revision ID: 17e05799f842
Revises: 33622715f72c
Create Date: 2026-05-06 21:53:22.416277

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = '17e05799f842'
down_revision: str | Sequence[str] | None = '33622715f72c'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'reaction_type',
        sa.Column('label', sa.String(length=120), nullable=True),
        sa.Column('image_url', sa.String(length=2048), nullable=False),
        sa.Column('sort_order', sa.Integer(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(
        op.f('ix_reaction_type_sort_order'), 'reaction_type', ['sort_order'], unique=False
    )
    op.create_table(
        'user_reaction',
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('reaction_type_id', sa.Integer(), nullable=False),
        sa.Column('target_kind', sa.String(length=32), nullable=False),
        sa.Column('target_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['reaction_type_id'], ['reaction_type.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'target_kind', 'target_id', name='uq_user_reaction_target'),
    )
    op.create_index(op.f('ix_user_reaction_user_id'), 'user_reaction', ['user_id'], unique=False)
    op.create_index(
        op.f('ix_user_reaction_reaction_type_id'),
        'user_reaction',
        ['reaction_type_id'],
        unique=False,
    )
    op.create_index(
        'ix_user_reaction_target',
        'user_reaction',
        ['target_kind', 'target_id'],
        unique=False,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('ix_user_reaction_target', table_name='user_reaction')
    op.drop_index(op.f('ix_user_reaction_reaction_type_id'), table_name='user_reaction')
    op.drop_index(op.f('ix_user_reaction_user_id'), table_name='user_reaction')
    op.drop_table('user_reaction')
    op.drop_index(op.f('ix_reaction_type_sort_order'), table_name='reaction_type')
    op.drop_table('reaction_type')
