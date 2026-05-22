-- Стандартная категория «Фильмы» для всех загружаемых пользователей (нужно для строк с явным user_card_category_id).
INSERT INTO user_card_category (user_id, name, created_at)
SELECT id, 'Фильмы', '2026-05-06 09:00:00'::timestamptz
FROM public."user"
ON CONFLICT ON CONSTRAINT uq_user_card_category_user_name DO NOTHING;
