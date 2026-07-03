# Profile Activity Heatmap

## Scope

GitHub-style activity heatmap on the profile **Statistics** tab showing completed watched films/games by day.

## Acceptance criteria

- Heatmap appears at the top of `Статистика`, above metric strip and charts.
- Only **completed** cards (`is_planned=false`) are counted; **Позже** / planned cards are excluded.
- Shelf filter reuses existing `category_id` vocabulary (`activity_category_id` on stats API).
- Tapping a day drills into rated cards list filtered by `completedOn` (+ shelf when selected).
- Mobile: horizontally scrollable compact grid with touch-friendly cells.
