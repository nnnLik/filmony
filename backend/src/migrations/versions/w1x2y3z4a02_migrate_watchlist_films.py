"""Migrate legacy user_watchlist_film into watchlist_entry.

Revision ID: w1x2y3z4a02
Revises: w1x2y3z4a01
"""

from collections.abc import Sequence

from alembic import op

revision: str = 'w1x2y3z4a02'
down_revision: str | Sequence[str] | None = 'w1x2y3z4a01'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        INSERT INTO watchlist_entry (
            user_id,
            card_id,
            provider_meta,
            watch_tag,
            watch_with_user_id,
            created_at,
            updated_at
        )
        SELECT
            uwf.user_id,
            CONCAT('kp:', f.kinopoisk_id) AS card_id,
            jsonb_build_object(
                'provider',
                'kinopoisk',
                'data',
                jsonb_build_object('kp_id', f.kinopoisk_id)
            ) AS provider_meta,
            'watch_later' AS watch_tag,
            NULL AS watch_with_user_id,
            uwf.created_at,
            uwf.created_at
        FROM user_watchlist_film AS uwf
        JOIN film AS f ON f.id = uwf.film_id
        ON CONFLICT (user_id, card_id) DO NOTHING
        """
    )


def downgrade() -> None:
    op.execute(
        """
        DELETE FROM watchlist_entry
        WHERE provider_meta ->> 'provider' = 'kinopoisk'
          AND watch_tag = 'watch_later'
        """
    )
