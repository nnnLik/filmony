# SQL-фикстуры для Postgres

Загрузка: из корня `make fixtures-load` (нужен контейнер **`homelab-postgres`**, homelab-infra `make dev-up`). Порядок — [`scripts/load-fixtures.sh`](../scripts/load-fixtures.sh).

## Порядок и зависимости

1. `user.sql` — пользователи.  
2. `reaction_type.sql` — каталог реакций (`ON CONFLICT (id) DO UPDATE`).  
3. `film.sql` — фильмы (`id` автоинкремент; в `movie_card` ссылаются на эти id).  
4. `movie_card.sql` — карточки (`(user_id, film_id)` уникальны); в конце файла — доп. карточки с `is_favorite` / общими фильмами.  
5. `movie_card_favorite_updates.sql` — пометка любимых у уже вставленных карточек (`UPDATE` по `user_id` + `film_id`).  
6. `user_watchlist_film.sql` — «хочу посмотреть», только `user` + `film`.  
7. `movie_card_comment.sql` — комментарии (текст до 100 символов), в т.ч. ответы (`parent_comment_id`).  
8. `user_reaction.sql` — реакции на карточки и комментарии (`movie_card`, `movie_card_comment`).  
9. `movie_card_tag.sql` — теги карточек.  
10. `user_subscription.sql` — подписки (пара `follower` → `following` уникальна).  
11. `feed_post.sql` — текстовые посты ленты (`ON CONFLICT (id) DO UPDATE`; в конце — `setval` для последовательности `id`).

## Объём (≈ после расширения соц. графа)

| Сущность            | Порядок величины |
|---------------------|------------------|
| Пользователи        | 14 строк (2 «живых» тестовых + 12 `fixture_*`) |
| Фильмы              | 29              |
| Карточки            | 65              |
| Любимые (`is_favorite`) | множество у разных авторов + отдельный `UPDATE` блок |
| Комментарии         | 126+            |
| Реакции (`user_reaction`) | 50+       |
| Теги                | 120+            |
| Подписки            | 46              |
| Watchlist           | 15              |
| Посты ленты (`feed_post`) | 8 (текст, в т.ч. с `referenced_movie_card_id` / `source_comment_id` / `image_url`) |

Повторная загрузка в **непустую** БД даст ошибки уникальности на `INSERT` (кроме `reaction_type`). Используйте чистую схему или точечную подгрузку одного файла: `./scripts/load-fixtures.sh user.sql`.

## Замечания по схеме

- Индексы и ограничения соответствуют миграциям Alembic (в т.ч. `user_watchlist_film`, уникальность карточки на пару пользователь+фильм, `movie_card.is_favorite` / `favorite_marked_at`).
