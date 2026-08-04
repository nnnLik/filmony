# Action log entry

- **Timestamp:** 2026-05-08
- **Feature slug:** `recent-views-copy-card-link`
- **Action type:** docs
- **Summary:** Фича: копирование t.me deep link на карточку (VITE_TELEGRAM_BOT_USERNAME), полоска «Недавно открывали» в localStorage; документация `docs/features/recent-views-copy-card-link.md`.
- **Files:** `docs/features/recent-views-copy-card-link.md`, `frontend/src/lib/miniAppCardDeepLink.ts`, `frontend/src/lib/copyTextToClipboard.ts`, `frontend/src/lib/recentCardViews.ts`, `frontend/src/components/feed/RecentCardsStrip.tsx`, `frontend/src/pages/FeedPage.tsx`, `frontend/src/pages/MovieCardDetailPage.tsx`, `frontend/src/components/share/ShareFollowersPicker.tsx`, `frontend/src/pages/ShareMovieCardPage.tsx`, `frontend/src/vite-env.d.ts`, `vars/.env.example`, `vars/.env.development`
- **Verification:** вручную по чеклисту в `docs/features/recent-views-copy-card-link.md`; при необходимости `npm run build` в `frontend/`.
