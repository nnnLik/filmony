# Action log entry

- **Timestamp:** 2026-05-08 (UTC approx.)
- **Feature slug:** `mvp-docs-alignment`
- **Action type:** docs
- **Summary:** Синхронизированы продуктовые документы с кодом: профиль и карточки не заглушки; Telegram ping vs Celery engagement; шаринг только на подписчиков (followers); реакции/комментарии в engagement; фронт auth через `useAuthStatus`; `.cursor/tech.md` §5–8 и `movie-card-create-flow` scope; переписан `.cursor/features/telegram-engagement-notifications/feature.md`.
- **Files:**
  - `docs/features/profile-and-public-profiles.md`
  - `docs/features/telegram-notifications.md`
  - `docs/features/telegram-user-base.md`
  - `docs/features/telegram-engagement-notifications.md`
  - `docs/features/profile-stats-details.md`
  - `.cursor/tech.md`
  - `.cursor/features/movie-card-create-flow/feature.md`
  - `.cursor/features/telegram-engagement-notifications/feature.md`
- **Verification:** правки текстовые; рекомендуется `make backend-test` при сомнениях в контрактах (не требуется для markdown-only).
