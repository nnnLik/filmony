# Result: profile-csv-export

## Что сделано

- Экспорт всех movie cards текущего пользователя в CSV (колонки: card_id, film_id, kinopoisk_id, title, year, genres `|`, rating, company, mood_before, mood_after, custom_tags `;`, poster_url, updated_at ISO). Кодировка `utf-8-sig`.
- Отправка файла в Telegram через multipart `sendDocument`; имя `filmony-cards-{slug}-{YYYYMMDD}.csv`.
- UI на [frontend/src/pages/ProfilePage.tsx](frontend/src/pages/ProfilePage.tsx): экспорт рядом с настройками, обработка `telegram_chat_unavailable` как на странице редактирования.

## Изменённые / новые файлы

- `backend/src/integrations/telegram/bot_api_client.py`
- `backend/src/services/telegram/send_bot_message.py`
- `backend/src/services/profile/list_user_movie_cards.py`
- `backend/src/services/profile/export_my_movie_cards_csv_telegram.py` (новый)
- `backend/src/api/profile/schemas.py`, `backend/src/api/profile/me_routes.py`
- `backend/src/tests/api/test_me_cards_export_csv.py` (новый)
- `frontend/src/api/profileApi.ts`, `frontend/src/pages/ProfilePage.tsx`
- `docs/features/profile-csv-export.md`
- `.cursor/features/profile-csv-export/feature.md`, `.cursor/active/profile-csv-export/*`

## Проверка

Локально (в Docker, если разрешено): `make backend-test-one target=src/tests/api/test_me_cards_export_csv.py`.

## Ограничения

- Очень большие выгрузки упираются в лимит размера документа Telegram (~50 MB); отдельной проверки размера нет.
