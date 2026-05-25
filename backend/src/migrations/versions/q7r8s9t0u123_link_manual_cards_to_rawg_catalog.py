"""link manual no_provider movie_card rows to unambiguous RAWG catalog_item

Data fix: remap manual cards created with provider=no_provider and NULL catalog linkage
when the trimmed normalized display_title resolves to exactly one RAWG catalog_item.

Revision ID: q7r8s9t0u123
Revises: c9d0e1f2a345
Create Date: 2026-05-25

"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = 'q7r8s9t0u123'
down_revision: str | Sequence[str] | None = 'c9d0e1f2a345'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        sa.text(
            r"""
/*
  Criteria (_TARGETS_):
    - movie_card.provider = 'no_provider'
    - catalog_item_id IS NULL, film_id IS NULL
    - non-empty display_title (trimmed)

  Normalization: lower(regexp_replace(btrim(display_title), '\s+', ' ', 'g'))

  Signal 1 (PRIMARY): normalized title equals that of another movie_card with
    provider='rawg', catalog_item_id IS NOT NULL, joined catalog_item has
    provider='rawg' AND game_id IS NOT NULL — kept only where global title maps
    to exactly one DISTINCT catalog_item_id.

  Signal 2 (FALLBACK): normalized title equals normalized game.name OR
    game.name_original via catalog_item (rawg + game_id) — global same
    unambiguous rule — used only when signal 1 is absent OR signal 2 agrees;
    SKIP if both signals exist and disagree.

  Per-user conflicts: SKIP if another row already has that catalog_item_id.
  Within this batch duplicate (user,catalog_item_id): pick lowest mc.id via DISTINCT ON.
*/

WITH norm_manual AS (
    SELECT
        id AS mc_id,
        user_id,
        lower(regexp_replace(btrim(display_title), '\s+', ' ', 'g')) AS nt
    FROM movie_card
    WHERE provider = 'no_provider'
      AND catalog_item_id IS NULL
      AND film_id IS NULL
      AND display_title IS NOT NULL
      AND btrim(display_title) <> ''
),

signal1_raw AS (
    SELECT
        lower(regexp_replace(btrim(mc.display_title), '\s+', ' ', 'g')) AS nt,
        mc.catalog_item_id AS catalog_item_id
    FROM movie_card AS mc
    INNER JOIN catalog_item AS ci ON ci.id = mc.catalog_item_id
    WHERE mc.provider = 'rawg'
      AND mc.catalog_item_id IS NOT NULL
      AND ci.provider = 'rawg'
      AND ci.game_id IS NOT NULL
      AND mc.display_title IS NOT NULL
      AND btrim(mc.display_title) <> ''
),

signal1_agg AS (
    SELECT
        nt,
        MIN(catalog_item_id) AS catalog_item_id
    FROM signal1_raw
    GROUP BY nt
    HAVING COUNT(DISTINCT catalog_item_id) = 1
),

signal2_flat AS (
    SELECT DISTINCT
        lower(regexp_replace(btrim(g.name), '\s+', ' ', 'g')) AS nt,
        ci.id AS catalog_item_id
    FROM catalog_item AS ci
    INNER JOIN game AS g ON g.id = ci.game_id
    WHERE ci.provider = 'rawg'
      AND ci.game_id IS NOT NULL
      AND g.name IS NOT NULL
      AND btrim(g.name) <> ''

    UNION

    SELECT DISTINCT
        lower(regexp_replace(btrim(g.name_original), '\s+', ' ', 'g')) AS nt,
        ci.id AS catalog_item_id
    FROM catalog_item AS ci
    INNER JOIN game AS g ON g.id = ci.game_id
    WHERE ci.provider = 'rawg'
      AND ci.game_id IS NOT NULL
      AND g.name_original IS NOT NULL
      AND btrim(g.name_original) <> ''
),

signal2_agg AS (
    SELECT
        nt,
        MIN(catalog_item_id) AS catalog_item_id
    FROM signal2_flat
    WHERE nt IS NOT NULL AND btrim(nt) <> ''
    GROUP BY nt
    HAVING COUNT(DISTINCT catalog_item_id) = 1
),

resolved AS (
    SELECT
        nm.mc_id,
        nm.user_id,
        nm.nt,
        s1.catalog_item_id AS ci_primary,
        s2.catalog_item_id AS ci_fallback
    FROM norm_manual AS nm
    LEFT JOIN signal1_agg AS s1 ON s1.nt = nm.nt
    LEFT JOIN signal2_agg AS s2 ON s2.nt = nm.nt
    WHERE nm.nt IS NOT NULL AND btrim(nm.nt) <> ''
),

chosen AS (
    SELECT
        mc_id,
        user_id,
        CASE
            WHEN ci_primary IS NOT NULL
                 AND ci_fallback IS NOT NULL
                 AND ci_primary <> ci_fallback
                THEN NULL
            WHEN ci_primary IS NOT NULL
                THEN ci_primary
            WHEN ci_fallback IS NOT NULL
                THEN ci_fallback
            ELSE NULL
        END AS catalog_item_id
    FROM resolved
),

picked_dup_batch AS (
    SELECT
        mc_id,
        user_id,
        catalog_item_id
    FROM chosen
    WHERE catalog_item_id IS NOT NULL
),

picked_one_per_user_ci AS (
    SELECT DISTINCT ON (user_id, catalog_item_id)
        mc_id,
        user_id,
        catalog_item_id
    FROM picked_dup_batch
    ORDER BY user_id, catalog_item_id, mc_id
),

final_pick AS (
    SELECT p.mc_id,
           p.user_id,
           p.catalog_item_id
    FROM picked_one_per_user_ci AS p
    WHERE NOT EXISTS (
        SELECT 1
        FROM movie_card AS other
        WHERE other.user_id = p.user_id
          AND other.catalog_item_id = p.catalog_item_id
          AND other.id <> p.mc_id
    )
)

UPDATE movie_card AS mc
SET
    catalog_item_id = ci.id,
    provider = ci.provider,
    external_id = ci.external_id
FROM final_pick AS fp
INNER JOIN catalog_item AS ci ON ci.id = fp.catalog_item_id
WHERE mc.id = fp.mc_id
"""
        )
    )


def downgrade() -> None:
    """Irreversible data repair: restoring prior provider/catalog linkage is unsafe."""

    pass
