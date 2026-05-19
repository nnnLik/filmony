# Feature: Profile statistics redesign

## Summary

The profile **Statistics** tab is a **single vertical page** (no inner Обзор/Вкусы/Рейтинги tabs): no large filter chrome at the top of stats (rated-card filters remain on **Cards → Оценённые**), a compact two-cell metric strip, `/stats` distributions (rating scale, taste polarity donut, tags, company/mood slices), ranking lists, and year bars with drill-down into the rated-cards query. Lists can still react to filters shared with the Cards tab (`RatedCardsListQuery`) for rankings, tags, company/mood taps, and year drill-down—without explanatory footnotes or sample-based shelf/provider/genre aggregates in the statistics view.

## User-visible behavior

### Layout

- **No stats header filters**: tuning sort, favorites, search, moods, shelf, etc. stays on **Оценённые**; statistics starts with compact KPIs (`ProfileStatsMetricStrip`) then charts and lists.
- **Metric strip**: only **Карточек** (`total_movies`) and **Средний балл** from `/stats`.
- **Polarity**: `TastePolarityChart` — conic donut plus minimal color bars with counts (no high/mid/low percentage prose).
- **Core sections**: rating histogram, polarity, popular tags (drill-down), company / mood-after rows (drill-down), top / worst lists, year distribution (drill-down).

### Owner vs public profile

- `enableCategoryFilter` is still passed where the parent distinguishes owner vs viewer; shelf-specific UI previously shared with statistics filters now lives under rated cards only.

### Wording

- Neutral labels where possible (**Компания**, **До**, **После**, **По годам выпуска**) in stats-adjacent copy and rated-cards filters where applicable.

### Drill-down

- Tags, company / mood-after rows, year bars → update shared query + `onDrillToRatedCards` where wired.
- When `RatedCardsListQuery` is not default: top/worst blocks use paired `getUserCards` requests (limits unchanged—see Technical notes).

### Empty and edge states

- Empty distributions → short «Пока нет данных» or targeted messages when a chosen filter omits aggregate slices.

## Technical notes

| Area | Detail |
|------|--------|
| Stats API | `getUserMovieCardStats(userId)` — unchanged; aggregate covers rating/year/tag/company/mood breakdowns returned by backend. |
| Filtered rankings | `useQuery` + `getUserCards` ×2 (`rating_desc` / `rating_asc`, limit 50) when `RatedCardsListQuery` is non-default. |
| Reusable filters | `ProfileStatsFilters.tsx` remains in codebase but is **not** mounted inside `ProfileStatsPanel` after this cleanup. |

## Verification

- `cd frontend && npm run lint` — must exit 0 with **no warnings** on touched files.
- `cd frontend && npm run build` — must exit 0.

Last regression pass: **2026-05-19** (`eslint .`, `tsc -b && vite build` succeeded).

Recommended manual smoke: narrow viewport; drill-down tags / company / mood / years; filtered top lists while filters differ from aggregate scope.

## Known limitations

- `/stats` does not accept client-side filter params: charts and KPIs reflect the aggregate scope from the backend, while tag/company/mood/year interactions adjust the Cards query and optionally switch to sampled top/worst lists when filters apply.
- Filtered top/worst lists remain approximate under pagination caps when many cards match.

## References

- Feature scope: `.cursor/features/profile-stats-redesign/feature.md`
- Implementation log: `.cursor/active/profile-stats-redesign/progress.md`, `.cursor/active/profile-stats-redesign/result.md`
