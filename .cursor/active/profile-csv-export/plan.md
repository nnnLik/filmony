# План: profile-csv-export

1. Расширить `TelegramBotApiClient` методом `send_document_multipart`, `SendTelegramBotMessageService.send_document`.
2. В `ListUserMovieCardsService` добавить `list_all_for_user` и поле `updated_at` в `MovieCardListItem`.
3. Сервис `ExportMyMovieCardsCsvTelegramService`: CSV + вызов Telegram.
4. Маршрут `POST /api/me/cards/export-csv` в `me_routes.py`.
5. Тесты `test_me_cards_export_csv.py` с моком `send_document_multipart`.
6. Фронт: `postExportMyCardsCsv`, UI на `ProfilePage.tsx`.
7. Документация и action-log.
