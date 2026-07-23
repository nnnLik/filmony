# Taste Quiz — «Угадай вкус» (taste-quiz-guess-rating)

## Metadata

- **Feature slug:** `taste-quiz-guess-rating`
- **Title:** Угадай вкус / Taste Quiz
- **Status:** shipped
- **Created at:** 2026-07-23
- **Target area:** backend + frontend + Telegram (invite / optional notify)

## Scope

Социальная мини-игра: guesser угадывает оценки owner по до **10 случайным rated-карточкам** за сессию (one-shot, без «жизней»). После каждого ответа — micro-reveal; в конце — summary. Между парами накапливается **Knowledge edge** (`points_sum` + `accuracy_pct`), отображается в stats (оба направления по подпискам) и рядом с ником в комментариях.

**Entry:**

- **Pull:** профиль друга / stats → «Угадать вкус» (guesser must follow owner).
- **Push:** owner → follower picker → invite + Telegram deep link (follow не обязателен, soft CTA).

**In scope:**

- Gate: owner ≥ 10 meaningful rated cards.
- Pool / anti-abuse: `played_card_ids` per pair, reset when unused < 10, one active session per pair.
- Snapshot card fields at session create; scoring exact / close (±0.5) / miss.
- Screens: gate, invite, guess, micro-reveal, session summary, stats, comment % enrichment.
- API: Check can play, Create session, Submit answer, Abandon, Get knowledge list, Get knowledge batch, Create invite, Resolve invite.
- Optional TG notify owner on quiz complete (default on).

**Non-goals:**

- Lives economy, global leaderboards, manual card pick.
- Exposing rating / mood_after / watch_note before answer.
- Taste match v2 / ML (`profile-taste-match` remains separate).

**Spec source of truth:** `docs/superpowers/specs/2026-07-23-taste-quiz-guess-rating-design.md`

## Acceptance Criteria

Implementation is complete when all items in the design spec **Acceptance criteria checklist** are satisfied. Summary:

### Backend (pytest inside Docker)

- Gate, follow vs invite paths, active session `409`, sampling + `played_card_ids` reset.
- Scoring 1 / 0.5 / 0 and edge `accuracy_pct` updates on submit and abandon.
- Snapshot immutability after session create.
- All eight API use-cases with documented request/response shapes.
- Knowledge list (both directions) and batch for comments (omit `attempts = 0`).

### Frontend

- `cd frontend && npm run lint && npm run build` — zero errors in touched files.
- Full screen flow: gate → guess (stepper ±0.5, no bottom nav) → reveal → summary.
- Stats block/page: «Я → они» / «Они → я».
- Comments: `(NN%)` with color scale; nothing if never played.
- Invite + deep link entry; pull requires follow.

### Docs & workflow

- `.cursor/active/taste-quiz-guess-rating/plan.md`, `progress.md`, `result.md` updated during delivery.
- Final feature doc: `docs/features/taste-quiz-guess-rating.md`.
- Action log entries per project workflow.
