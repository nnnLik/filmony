# Угадай вкус (Taste Quiz)

**Feature slug:** `taste-quiz-guess-rating`  
**Status:** shipped

## Overview

Социальная мини-игра: подписчик (или приглашённый по deep link) угадывает **оценки владельца** по **10 случайным карточкам** за сессию. После каждого ответа — micro-reveal; в конце — summary. Между парами накапливается **Knowledge edge** (сумма очков + меткость %).

## Как играть

1. **Pull:** на профиле друга (если подписан) — «Угадать вкус».
2. **Push:** на своём профиле — «Пригласить угадать» → ссылка `startapp=tq…` в Telegram.
3. Сессия: постер + улики (`company`, `mood_before`) → stepper ±0.5 → reveal → итог.
4. Повтор: когда неиспользованных карт < 10, пул перемешивается заново.

## Скоринг

| Результат | Очки |
|-----------|------|
| Точное совпадение | 1 |
| \|Δ\| = 0.5 | 0.5 |
| Иначе | 0 |

Меткость = `points_sum / attempts` (показывается в stats и как `(72%)` у ников в комментариях, если уже играли).

## Ограничения

- У владельца нужно **≥ 10** карточек с оценкой.
- Одна активная сессия на пару guesser→owner.
- Оценка / mood_after / заметка не показываются до ответа.

## API

Prefix: `/api/taste-quiz`

- `GET /can-play`, `POST /sessions`, `GET /sessions/{id}`, `POST /sessions/{id}/answers`, `POST /sessions/{id}/abandon`
- `GET /knowledge`, `POST /knowledge/batch`
- `POST /invites`, `GET /invites/{token}`

## Frontend routes

- `/taste-quiz/play/:ownerId`
- `/taste-quiz/invite`, `/taste-quiz/invite/:inviteToken`
- `/taste-quiz/stats`

## Spec & plan

- Design: [docs/superpowers/specs/2026-07-23-taste-quiz-guess-rating-design.md](../superpowers/specs/2026-07-23-taste-quiz-guess-rating-design.md)
- Plan: [docs/superpowers/plans/2026-07-23-taste-quiz-guess-rating.md](../superpowers/plans/2026-07-23-taste-quiz-guess-rating.md)
