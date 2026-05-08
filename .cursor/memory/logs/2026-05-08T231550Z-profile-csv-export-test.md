# Action log — profile-csv-export — test

- **Timestamp:** 2026-05-08T231550Z
- **Feature slug:** profile-csv-export
- **Action type:** test
- **Summary:** Добавлены API-тесты экспорта CSV с моком `TelegramBotApiClient.send_document_multipart`; хелпер читает `document_bytes` из позиционных аргументов вызова.
- **Files:** `backend/src/tests/api/test_me_cards_export_csv.py`
- **Verification:** `make backend-test-one target=src/tests/api/test_me_cards_export_csv.py` (запуск не выполнялся агентом).
