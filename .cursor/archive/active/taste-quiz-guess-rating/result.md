# Taste Quiz — result

**Status:** done  
**Feature slug:** `taste-quiz-guess-rating`  
**Completed:** 2026-07-23

## Implemented

- **Backend:** SQLAlchemy models + Alembic migration; 9 services (can-play, create/get/abandon session, submit answer, knowledge list/batch, create/resolve invite); `/api/taste-quiz/*` routes; Celery TG notify on session complete; deep link `startapp=tq{token}`.
- **Frontend:** play loop (gate → guess → reveal → summary), invite + landing pages, stats page (Я→они / Они→я), profile CTAs, `(NN%)` knowledge badges in comments, Telegram start-param redirect for `tq`.
- **Game rules:** 10-card sessions, scoring 1 / 0.5 / 0, pair progress with recycle when unused < 10, gate ≥10 rated cards, one active session per pair.

## Changed files (high level)

**Backend:** `backend/src/models/taste_quiz_*`, `backend/src/migrations/versions/c4d5e6f7a890_taste_quiz.py`, `backend/src/services/taste_quiz/*`, `backend/src/api/taste_quiz/*`, `backend/src/services/telegram/send_taste_quiz_complete_notification.py`, `backend/src/services/telegram/mini_app_link.py`, `backend/src/tasks/telegram_engagement.py`, `backend/src/api/router.py`

**Frontend:** `frontend/src/api/tasteQuiz*`, `frontend/src/components/tasteQuiz/*`, `frontend/src/pages/TasteQuiz*.tsx`, `frontend/src/hooks/useTasteQuiz*.ts`, `frontend/src/lib/tasteQuiz*`, `frontend/src/lib/miniAppCardDeepLink.ts`, `frontend/src/routes.tsx`, `frontend/src/navigation/TelegramMiniAppStartParamRedirect.tsx`, profile/feed/comment integration files

**Docs:** `docs/features/taste-quiz-guess-rating.md`, `docs/superpowers/plans/2026-07-23-taste-quiz-guess-rating.md`

## Verification

```bash
make backend-test-one target=src/tests/api/test_taste_quiz_routes.py   # 11 passed
make backend-test-one target=src/tests/services/taste_quiz/test_scoring.py  # 9 passed
cd frontend && npm run lint && npm run build  # exit 0
```

## Known limitations

- TG complete notify always on (no user toggle in v1).
- Invite API creates one token; multi-follower share is client-side via picker + share URL.
- Resolve invite requires authenticated session (Mini App always logged in).

## Next steps (optional)

- User setting to disable quiz-complete TG notify.
- Dedicated Celery task to push invite messages to selected followers (like card share).
