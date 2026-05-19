## Timestamp

2026-05-19T232000Z

## Feature slug

profile-stats-redesign

## Action type

code

## Summary

Статистика профиля: нейтральные подписи (Компания / До / После / годы выпуска), три компактных блока метаданных из одной страницы списка карточек (полки, provider, жанры каталога), без изменений бэкенда.

## Files

- `frontend/src/components/profile/ProfileStatsPanel.tsx`
- `frontend/src/components/profile/ProfileStatsFilters.tsx`
- `frontend/src/components/profile/ProfileRatedCardsFilters.tsx`
- `frontend/src/lib/profileStatsCardListSampleAggregates.ts`
- `docs/features/profile-stats-redesign.md`
- `.cursor/active/profile-stats-redesign/progress.md`
- `.cursor/active/profile-stats-redesign/result.md`

## Verification

```bash
cd frontend && npm run lint && npm run build
```

Exit code 0.
