# Action log

- **Timestamp:** 2026-05-07T20:05:00Z
- **Feature slug:** `feed-reaction-ui`
- **Action type:** `docs` + `code`

## Summary
Исправлено визуальное смещение иконки реакции в `IconButton` (flex-центрирование, z-index над ripple, `block` на SVG). Добавлена документация для агентов: `docs/frontend/ui-conventions.md`, обновлены `.cursor/tech.md`, `.cursor/rules/frontend-react-telegram-ui-standards.mdc`, `docs/features/movie-card-custom-reactions.md`.

## Files
- `frontend/src/components/reactions/ReactionStrip.tsx`
- `docs/frontend/ui-conventions.md` (new)
- `.cursor/tech.md`
- `.cursor/rules/frontend-react-telegram-ui-standards.mdc`
- `docs/features/movie-card-custom-reactions.md`

## Verification
- `cd frontend && npm run build` (run after merge with local changes)
