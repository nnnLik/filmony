# 2026-05-06T20:58:00Z

- Feature slug: `movie-card-edit-delete`
- Action type: test
- Summary: Добавлены API тесты на PATCH/DELETE карточки: auth, ownership, validation, not found и post-delete поведение.
- Files:
  - `backend/src/tests/api/test_cards_routes.py`
- Verification:
  - Добавленные тестовые кейсы ревьюнуты.
  - Запуск `make backend-test-one target=src/tests/api/test_cards_routes.py` требуется вручную (терминальные команды недоступны в текущей сессии).
