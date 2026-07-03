# Telegram Digest Подписанной Активности

## Metadata
- Feature slug: `subscribed-activity-telegram-digest`
- Title: Telegram Digest Подписанной Активности
- Status: planned
- Author: `r.makkhmudov`
- Created at: `2026-07-03`
- Priority: high
- Target area: backend / telegram / celery

## Problem Statement
Пользователь подписывается на других людей, но текущие Telegram-уведомления работают только на отдельные публикации. Из-за этого важные обновления быстро теряются, а лента уведомлений выглядит слишком шумной и реактивной.

Нужен компактный дайджест раз в 48 часов, который собирает активность людей, на которых подписан пользователь, и отправляет в Telegram не сырой список карточек, а короткую подборку из 3 самых интересных инсайтов. Дайджест должен быть полезным даже при умеренной активности и не должен выглядеть как спам.

## Goals
- Раз в 48 часов отправлять подписанному пользователю один Telegram DM с дайджестом активности.
- Собрать дайджест из нескольких типов сигналов, а не только из списка просмотренных фильмов.
- Выбирать 3 пункта из scored pool случайно, но под контролем качества и разнообразия.
- Использовать уже существующую архитектуру сервисов, Celery и Telegram delivery.
- Иметь дедупликацию, чтобы один и тот же пользователь не получал повторный дайджест раньше срока.

## Non-Goals
- Не делаем новый пользовательский интерфейс в вебе.
- Не добавляем ручные настройки частоты, фильтров или тем дайджеста на первом шаге.
- Не меняем existing follower publish notifications и mention DM flows.
- Не строим месячную сводку, shareable recap или profile card export; это отдельная фича.

## User-Facing Behavior
Пользователь получает Telegram-сообщение примерно каждые 48 часов, если у него есть подписки и есть что показать. Сообщение короткое: заголовок, 3 выбранных инсайта и CTA на приложение.

Если за окно нет достаточно хороших сигналов, дайджест не отправляется, а состояние окна отмечается как обработанное, чтобы не пытаться слать пустой шум.

### Пример 1: нормальный дайджест
```text
🔔 За последние 48 часов у людей, на которых вы подписаны, появилось интересное:

1. <b>Аня</b> подняла оценку «Дюны» до 9 и добавила её в любимое
2. <b>Макс</b> опубликовал пост: «Наконец-то добрался до новой части — коротко и по делу»
3. <b>Ирина</b> собрала новую подборку в карточке «Лучшие осенние фильмы»

Открыть подборку в Filmony: <a href="...">перейти</a>
```

### Пример 2: мало данных
```text
🔔 За последние 48 часов у людей, на которых вы подписаны, было мало новой активности.

Мы покажем следующий дайджест, когда наберётся более интересная подборка.
```

### Пример 3: без Telegram-бота / fallback
Если Telegram bot username недоступен, текст остаётся тем же, но CTA заменяется на plaintext-упоминание открыть приложение из Telegram без deep link.

## Data Sources And Aggregation Rules
Дайджест собирается только по людям, на которых подписан получатель.

Основные источники данных:
- новые user cards подписанных авторов;
- новые feed posts подписанных авторов;
- профильные агрегаты автора, если они помогают сформировать инсайт;
- counts / stats, которые уже считаются в profile services.

Рекомендуется переиспользовать существующие сервисы и их данные:
- `backend/src/services/subscriptions/list_follower_user_ids_for_following_user.py`
- `backend/src/services/profile/get_user_card_stats.py`
- `backend/src/services/profile/get_user_profile_counts.py`
- `backend/src/services/profile/list_user_feed_posts.py`
- `backend/src/api/profile/schemas.py`

Агрегация должна работать по окну последних 48 часов от `last_digest_sent_at` или от `now - 48h`, если дайджест для пользователя ещё не отправлялся.

Правила агрегирования:
- Группировать события по автору и типу инсайта.
- Учитывать только новые события, которых пользователь ещё не видел в предыдущем дайджесте.
- Считать одним автором только одну сильную карточку, если несколько сигналов от одного и того же пользователя выглядят дублирующимися.
- Если у автора есть несколько candidates одного типа, оставлять максимум один per author per category в финальной выборке.
- Игнорировать слабые / пустые сигналы, которые не проходят quality threshold.

## Insight Pool
Дайджест не должен быть «сырым списком просмотренных фильмов». Вместо этого строится pool из разных категорий инсайтов, а затем из него выбираются 3 пункта.

### Candidate categories
1. **Новая карточка автора**
   - новая карточка фильма / игры / другого supported item;
   - лучше всего подходит, если у карточки есть title, poster, rating или tags.
2. **Новый пост в ленте**
   - короткий текстовый инсайт из feed post;
   - можно использовать snippet, если текст длинный.
3. **Сильный профильный сигнал**
   - заметный рост средней оценки / изменение распределения оценок;
   - новая интересная верхняя / нижняя карточка из stats;
   - всплеск по тегам, категориям или «любимым» подборкам.
4. **Сводный авторский сигнал**
   - «за 48 часов автор добавил N карточек и опубликовал M постов»;
   - допустим только как запасной вариант, если pool слабый.

### Scoring
Каждый candidate получает score, который учитывает:
- свежесть события;
- тип события;
- качество контента;
- разнообразие относительно уже выбранных candidate;
- авторскую уникальность;
- вероятность, что пользователь сочтёт сигнал интересным.

Порог качества:
- события с пустым текстом, без title или без meaningful metadata не попадают в pool;
- однотипные сигналы от одного автора не должны вытеснять более разнообразные;
- если pool слишком большой, кандидаты предварительно обрезаются до top-N по score.

### Random selection logic
Нужно оставить ощущение случайности, но без мусорной выборки:
- сначала строится ranked pool;
- кандидаты разбиваются по категориям;
- из каждой категории выбираются лучшие варианты above threshold;
- финальные 3 пункта выбираются weighted random из top-ranked pool с ограничениями:
  - максимум 1 пункт на автора;
  - максимум 2 пункта одного типа;
  - минимум 2 разных автора, если это возможно;
  - при сильном дефиците данных допускается 1 или 2 пункта, но не больше одного пустого сигнала.

Для стабильности retries желательно использовать deterministic seed, завязанный на `recipient_user_id + digest_window_start`, чтобы повторная обработка окна не меняла текст произвольно.

## Cadence, Anti-Spam, Deduplication
- Базовая частота: один дайджест раз в 48 часов на пользователя.
- Отправка только если у пользователя есть хотя бы одна подписка и хотя бы один qualifying candidate.
- После успешной отправки сохраняется `last_digest_sent_at` и идентификатор окна.
- Повторный запуск задачи не должен создать дубликат, если окно уже было обработано.
- Если доставка в Telegram не удалась по временной причине, задача может быть повторена; при этом selection должен оставаться стабильным для того же окна.
- Если у пользователя нет активного Telegram link, дайджест не отправляется и не считается ошибкой бизнес-уровня.
- Если пользователь не подписан ни на кого, дайджест не формируется.

## Backend Architecture
### Services
Рекомендуется вынести orchestration в отдельный сервис, например:
- `BuildSubscribedActivityTelegramDigestService`
- `SelectSubscribedActivityDigestCandidatesService`
- `SendSubscribedActivityTelegramDigestService`

Один orchestrator должен:
1. загрузить список подписок получателя;
2. собрать кандидаты по followed users;
3. отсечь слабые или дублирующиеся сигналы;
4. выбрать 3 пункта;
5. отрендерить Telegram HTML;
6. отправить сообщение через existing Telegram service;
7. сохранить digest state.

Ожидается reuse:
- `backend/src/services/subscriptions/list_follower_user_ids_for_following_user.py` для follower resolution;
- `backend/src/services/telegram/send_bot_message.py` для доставки;
- profile stats / feed post services как источники фактов или шаблон для нового aggregator service.

### Celery task
Нужен отдельный Celery task в духе `backend/src/tasks/telegram_engagement.py`, который:
- запускается по расписанию;
- находит пользователей, которым пора отправить digest;
- вызывает digest service для каждого due recipient;
- изолирует ошибки по пользователю, чтобы один failing recipient не валил весь batch.

Task scheduling can be implemented with Celery beat or an existing scheduler entrypoint. На уровне этой фичи требуется только фоновой workflow; новые HTTP endpoints не требуются.

### Routes / views
Новых HTTP route/view не нужно.

Если позже понадобится preview или settings endpoint, это должно быть отдельной фичей и отдельным API contract; в рамках этой задачи не планируется ни `/api/.../digest`, ни UI для управления частотой.

## Model / Storage Needs
Нужно добавить durable storage для состояния дайджеста. Минимально требуется:
- `recipient_user_id`
- `last_digest_sent_at`
- `last_digest_window_start`
- `last_digest_window_end`
- `last_digest_payload_hash` или другой idempotency marker
- `last_successful_delivery_at`
- `failed_attempts` / `last_error_at` для наблюдаемости, если это полезно для операционной поддержки

Вариант реализации может быть отдельной таблицей состояния digest per user. Если будет проще, допустима компактная таблица с одной строкой на получателя и обновлением после успешной доставки.

Если для детекции дубликатов понадобится materialized event log или snapshot таблица кандидатов, это тоже должно быть описано в миграции и сервисе, но без избыточной денормализации на старте.

## Tests
Фича должна быть покрыта pytest-тестами на уровне сервисов, task orchestration и Telegram delivery.

### Обязательные тесты
- сервис формирования кандидатов: набор data sources, scoring, filtering, dedupe;
- сервис выбора 3 items: weighted randomness, category caps, author caps, fallback при низком объёме;
- service для отправки Telegram digest: success path, chat unavailable, transport failure;
- Celery task: due recipients, non-due recipients, one recipient failure does not break batch;
- storage/state update: successful send updates digest state, repeat run does not resend same window;
- edge cases: no subscriptions, no qualifying candidates, fewer than 3 candidates, missing Telegram user id.

### Existing patterns to reuse in tests
- `backend/src/tests/api/test_follower_publish_telegram_notifications.py`
- `backend/src/tests/api/test_cards_routes.py`
- `backend/src/tests/api/test_profile_routes.py`

### Regression coverage expectations
- publish notifications for cards/posts remain unchanged;
- digest task does not duplicate publish-time notifications;
- Telegram `send_bot_message` reuse still respects unavailable-chat behavior;
- profile stats / feed-post source services can be reused without changing existing contracts.

## Acceptance Criteria
- [ ] Дайджест отправляется раз в 48 часов подписанным пользователям, у которых есть Telegram link и qualifying activity.
- [ ] Дайджест содержит ровно 3 выбранных инсайта, если pool позволяет.
- [ ] Выборка основана на scored pool и случайности с ограничениями по качеству.
- [ ] Повторы task не создают дубликаты в пределах одного окна.
- [ ] Новых HTTP routes не требуется, и это явно зафиксировано в реализации.
- [ ] Все новые и изменённые backend behaviors покрыты pytest-тестами.

## References
- `backend/src/tasks/telegram_engagement.py`
- `backend/src/services/subscriptions/list_follower_user_ids_for_following_user.py`
- `backend/src/services/telegram/send_bot_message.py`
- `backend/src/services/profile/get_user_card_stats.py`
- `backend/src/services/profile/get_user_profile_counts.py`
- `backend/src/services/profile/list_user_feed_posts.py`
- `backend/src/api/profile/schemas.py`
- `backend/src/tests/api/test_profile_routes.py`
- `backend/src/tests/api/test_follower_publish_telegram_notifications.py`
- `backend/src/tests/api/test_cards_routes.py`
- `docs/features/followed-content-notifications.md`
