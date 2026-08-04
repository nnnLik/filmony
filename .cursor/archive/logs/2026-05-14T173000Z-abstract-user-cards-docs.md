# Action log fragment

- **Timestamp:** 2026-05-14T173000Z
- **Feature slug:** abstract-user-cards
- **Action type:** docs

## Summary

Aligned frontend TypeScript and product docs with backend **UserCard** **`provider`** (`kinopoisk` | `no_provider`) and nullable **`external_id`**: `MovieCard` / create payloads / catalog resolve client typing; Kinopoisk button uses **`kinopoiskTitleUrlFromCard`**; manual create sends **`provider: no_provider`**. Documented CSV **`provider`/`external_id`** columns and resolve rejection of **`no_provider`**.

## Files

- `frontend/src/api/profileTypes.ts` — `UserCardProvider`; `MovieCard.provider`, `external_id`
- `frontend/src/api/cardApi.ts` — `CreateMovieCardKinopoiskPayload`; manual payload `provider: no_provider`
- `frontend/src/api/catalogApi.ts` — `CatalogResolveRequestProvider`; typed resolve
- `frontend/src/lib/movieCardDisplay.ts` — `kinopoiskNumericIdFromCard` for KP affordance
- `frontend/src/lib/openExternalUrl.ts` — `kinopoiskNumericIdFromCard`, `kinopoiskTitleUrlFromCard`
- `frontend/src/pages/CreateCardPage.tsx` — explicit **`no_provider`** on manual POST
- `frontend/src/pages/MovieCardDetailPage.tsx` — KP open via **`kinopoiskTitleUrlFromCard`**
- `docs/features/abstract-user-cards.md`
- `.cursor/active/abstract-user-cards/result.md`
- `.cursor/active/abstract-user-cards/progress.md`
- `.cursor/memory/logs/action-log.md`

## Verification

- `cd frontend && npm run lint && npm run build` — **exit 0**
- Backend: **223 passed** (`pytest` in Docker) and **ruff** clean from prior slice (`.cursor/memory/logs/2026-05-14T163000Z-abstract-user-cards-code.md`); not re-run this session

## Links

- `docs/features/abstract-user-cards.md`
- `.cursor/active/abstract-user-cards/result.md`
