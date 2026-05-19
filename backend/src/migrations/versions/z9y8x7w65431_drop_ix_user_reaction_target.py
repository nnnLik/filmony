"""Drop redundant user_reaction btree index superseded by composite window index.

Revision ID: z9y8x7w65431
Revises: r0s1t2u3v456

Evidence summary (production validation checklist):

- Query shapes from ``GetReactionSummariesForTargetsService`` aggregate reactions with
  ``WHERE (target_kind, target_id) IN (...)`` OR scopes and optional ``user_id`` filters.
- ``ix_user_reaction_target_kind_type_id`` begins with ``(target_kind, target_id, ...)`` so PostgreSQL
  can satisfy prefix predicates on ``(target_kind, target_id)`` without the narrower standalone
  ``ix_user_reaction_target`` index.
- **Keep** ``ix_user_reaction_user_target_kind`` for viewer-scoped lookups by ``user_id``.
- **Keep** ``ix_user_reaction_target_kind_type_id`` for partitioned reactor ordering / counts.
- **Keep** ``ix_user_reaction_reaction_type_id`` for FK/maintenance paths referencing ``reaction_type``.
- Run after deployment::

    SELECT indexrelname, idx_scan, idx_tup_read,
           pg_relation_size(indexrelid) AS bytes
    FROM pg_stat_user_indexes
    WHERE schemaname = 'public' AND relname = 'user_reaction'
    ORDER BY indexrelname;

    EXPLAIN (ANALYZE, BUFFERS)
    SELECT target_kind, target_id, reaction_type_id, COUNT(*)
    FROM user_reaction
    WHERE target_kind = 'CARD' AND target_id = 1
    GROUP BY target_kind, target_id, reaction_type_id;

Expect ``Index Scan`` / ``Bitmap Index Scan`` on ``ix_user_reaction_target_kind_type_id`` (or bitmap
OR across partitions), not ``ix_user_reaction_target``. Local ``docker compose exec backend``
statistics were unavailable during migration authoring; capture ``pg_stat_user_indexes`` post-warmup to
confirm ``idx_scan`` on ``ix_user_reaction_target`` stayed at zero before drop.
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = 'z9y8x7w65431'
down_revision: str | Sequence[str] | None = 'r0s1t2u3v456'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_index('ix_user_reaction_target', table_name='user_reaction')


def downgrade() -> None:
    op.create_index(
        'ix_user_reaction_target',
        'user_reaction',
        ['target_kind', 'target_id'],
        unique=False,
    )
