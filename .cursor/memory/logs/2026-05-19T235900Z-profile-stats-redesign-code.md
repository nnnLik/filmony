Timestamp: **2026-05-19T235900Z** (UTC proxy)

Feature slug: `profile-stats-redesign`

Action type: `code`

## Summary

Статистика профиля: убран верхний блок `ProfileStatsFilters`, сносные подсказки про агрегат/выборку и блоки «Полки / Источник / Жанры» на клиентской выборке; полоса метрик — только «Карточек» и «Средний балл»; полярность — кольцо + компактные счётчики без процентов «стеной». Удалён неиспользуемый `frontend/src/lib/profileStatsCardListSampleAggregates.ts`. Компонент `ProfileStatsFilters.tsx` сохранён для возможного переиспользования, из панели статистики не рендерится.

## Files

- `frontend/src/components/profile/ProfileStatsPanel.tsx`
- `frontend/src/components/profile/ProfileStatsCharts.tsx`
- `frontend/src/components/profile/ProfileStatsSummaryCard.tsx`
- `frontend/src/lib/profileStatsCardListSampleAggregates.ts` (deleted)
- `.cursor/active/profile-stats-redesign/progress.md`
- `.cursor/active/profile-stats-redesign/result.md`
- `docs/features/profile-stats-redesign.md`
- `.cursor/memory/logs/action-log.md`

## Verification

```bash
cd frontend && npm run lint
# exit 0

cd frontend && npm run build
# exit 0
```
