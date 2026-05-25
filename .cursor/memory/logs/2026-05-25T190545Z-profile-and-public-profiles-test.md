# Action log fragment

**Timestamp:** 2026-05-25T19:05:45Z  
**Feature slug:** profile-and-public-profiles  
**Action type:** test

## Summary
Расширены API-тесты публичного списка полок: 401 без сессии, 404, чужой зритель видит полки автора, ответ включает коммитнутую после POST полку.

## Files
- `backend/src/tests/api/test_profile_routes.py`

## Verification
- `docker exec -w /opt/app/src filmony-backend pytest tests/api/test_profile_routes.py::test_public_user_card_categories_requires_auth tests/api/test_profile_routes.py::test_public_user_card_categories_404_unknown_user tests/api/test_profile_routes.py::test_public_user_card_categories_returns_owner_shelves tests/api/test_profile_routes.py::test_public_user_card_categories_lists_committed_shelves -q`
