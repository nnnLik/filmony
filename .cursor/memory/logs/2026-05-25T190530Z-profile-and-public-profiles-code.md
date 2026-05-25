# Action log fragment

**Timestamp:** 2026-05-25T19:05:30Z  
**Feature slug:** profile-and-public-profiles  
**Action type:** code

## Summary
Публичный список полок (`GET /api/users/{user_id}/card-categories`), сервис `ListPublicUserCardCategoriesService`, фронт: `getUserPublicCardCategories`, ключ кеша React Query и доработка `ProfileRatedCardsFilters`/`PublicProfilePage`.

## Files
- `backend/src/services/user_card_categories/list_public_user_card_categories.py`
- `backend/src/services/user_card_categories/__init__.py`
- `backend/src/api/profile/users_routes.py`
- `frontend/src/api/profileApi.ts`
- `frontend/src/api/profileTypes.ts`
- `frontend/src/feed/feedQueryKeys.ts`
- `frontend/src/components/profile/ProfileRatedCardsFilters.tsx`
- `frontend/src/pages/PublicProfilePage.tsx`
- `frontend/src/pages/ProfilePage.tsx`

## Verification
- `docker exec -w /opt/app/src filmony-backend ruff check --config /opt/app/pyproject.toml api/profile/users_routes.py` (imports fixed)
- `cd frontend && npm run lint && npm run build`
