# Social Depth Pack — progress

## 2026-07-29
- Weekly controversy Telegram upgrade: film deeplink `f{id}`, enriched message (polar cards, intro variants, viewer personalization, runner-up), inline button, spread≥4 gate, `link_card_id` persistence.
- Backend tests: `test_build_weekly_controversy_message.py`, `test_weekly_controversy_routes.py`, `test_mini_app_link.py` — pass in Docker.
- Frontend: ESLint pass; film start_param redirect in `TelegramMiniAppStartParamRedirect.tsx`.
- Migration `e6f7a8b90123` applied.

## 2026-07-28
- Completed all four slices (A overlap, B co-view, C controversy, D streak).
- Backend: 535 pytest passed in Docker.
- Frontend: lint + build pass.
- Docs: `docs/features/social-depth-pack.md`, `result.md`.
