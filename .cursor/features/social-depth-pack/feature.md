# Social Depth Pack

## Scope
- Watchlist overlap discovery (mutual subscriptions) with «Смотрим вместе» CTA.
- Co-view sessions: post-watch feed post with split ratings among participants.
- Weekly controversial title in following circle (Telegram + in-app chip).
- Rating streak badge (fire + number, visible at 4+ days) app-wide next to nicks.

## Acceptance Criteria
- `GET /api/me/watchlist/overlaps` returns mutual watchlist overlaps with partner list.
- Watch-with invite creates `watch_session`; rated participants trigger co-view feed post with splits.
- Weekly controversy digest + `GET /api/me/weekly-controversy` chip on film community.
- `POST /api/streaks/batch` returns streaks ≥4; badge on all nick surfaces with heat animation capped at 10.
- pytest coverage for all new backend behavior; frontend lint/build pass.
