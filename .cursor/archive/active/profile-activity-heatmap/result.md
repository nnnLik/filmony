# Profile Activity Heatmap — Result

**Status:** done

## Implemented

- GitHub-style yearly activity grid on profile **Статистика** tab.
- Completed-only aggregation (`is_planned=false`); planned/watchlist cards excluded.
- Shelf filter on heatmap via existing category ids.
- Day tap → rated cards tab with `completedOn` + optional `categoryId` URL filters.

## Changed files

- `backend/src/models/user_card.py`
- `backend/src/migrations/versions/y3z4a5b6c789_user_card_completed_at.py`
- `backend/src/services/profile/get_user_card_stats.py`
- `backend/src/services/profile/list_user_cards.py`
- `backend/src/services/cards/create_user_card.py`
- `backend/src/api/profile/schemas.py`
- `backend/src/api/profile/users_routes.py`
- `backend/src/tests/api/test_profile_routes.py`
- `frontend/src/components/profile/ProfileActivityHeatmap.tsx`
- `frontend/src/components/profile/ProfileStatsPanel.tsx`
- `frontend/src/lib/activityHeatmapGrid.ts`
- `frontend/src/lib/ratedCardsListQuery.ts`
- `frontend/src/api/profileTypes.ts`
- `frontend/src/api/profileApi.ts`
- `frontend/src/lib/__tests__/activityHeatmapGrid.test.ts`
- `frontend/src/lib/__tests__/ratedCardsListQuery.test.ts`

## Verification

- `make backend-test-one target=src/tests/api/test_profile_routes.py::test_user_stats_activity_heatmap_excludes_planned_cards` — PASS
- `make backend-test-one target=src/tests/api/test_profile_routes.py::test_user_stats_activity_heatmap_filters_by_shelf` — PASS
- `make backend-test-one target=src/tests/api/test_profile_routes.py::test_list_user_cards_filter_by_completed_on` — PASS
- `cd frontend && npm run lint && npm run build` — PASS
- `npm run test -- --run src/lib/__tests__/activityHeatmapGrid.test.ts src/lib/__tests__/ratedCardsListQuery.test.ts` — PASS

## Limitations

- Heatmap uses film-backed stats join for shelf names; game-only cards follow same completion rules but may be underrepresented in legacy stats joins.
- Activity window is fixed at 90 days (~3 months, UTC).
