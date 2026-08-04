# Action log — profile-csv-export — code

- **Timestamp:** 2026-05-08T231500Z
- **Feature slug:** profile-csv-export
- **Action type:** code
- **Summary:** Экспорт карточек в CSV через Telegram (`sendDocument`), endpoint `POST /api/me/cards/export-csv`, UI на профиле с `IconButton` + обработка ошибок бота.
- **Files:**
  - `backend/src/integrations/telegram/bot_api_client.py`
  - `backend/src/services/telegram/send_bot_message.py`
  - `backend/src/services/profile/list_user_movie_cards.py`
  - `backend/src/services/profile/export_my_movie_cards_csv_telegram.py`
  - `backend/src/api/profile/schemas.py`
  - `backend/src/api/profile/me_routes.py`
  - `backend/src/tests/api/test_me_cards_export_csv.py`
  - `frontend/src/api/profileApi.ts`
  - `frontend/src/pages/ProfilePage.tsx`
- **Verification:** запуск pytest в контейнере: `make backend-test-one target=src/tests/api/test_me_cards_export_csv.py` (не выполнялся агентом в среде без команд).
