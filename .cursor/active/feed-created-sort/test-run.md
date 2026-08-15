# feed-created-sort — Docker lint + pytest run

Date: 2026-08-15  
Repo: `/Users/r.makkhmudov/Projects/github/filmony`  
Runner: Docker (`filmony-backend` already Up 9 hours; `make start` not needed)

Compose status before run:

```
filmony-backend backend Up 9 hours
filmony-celery-worker-1 celery-worker Up 9 hours
filmony-rustfs-1 rustfs Up 9 hours
```

Migration: tests did **not** fail on a missing index. Failures below are assertion mismatches on feed chronology (`movie_card` vs `feed_post`). Alembic via fixture was not required as a separate step.

---

## 1. Ruff (targeted)

**Command**

```bash
docker compose -f docker-compose.yml exec -w /opt/app/src backend ruff check \
  services/feed/list_global_feed.py \
  services/cards/list_user_card_feed.py \
  services/profile/list_user_cards.py \
  models/user_card.py \
  migrations/versions/j8k9l0m1n234_user_card_completed_at_feed_indexes.py \
  tests/integration/api/test_global_feed_routes.py \
  tests/integration/api/test_movie_card_feed_recommendation.py \
  tests/integration/api/test_profile_routes.py
```

**Exit code:** `0`  
**Result:** All checks passed!

---

## 2. Pytest: global feed routes

**Command**

```bash
make backend-test-one target=src/tests/integration/api/test_global_feed_routes.py
```

Expanded:

```bash
docker exec -w /opt/app filmony-backend uv run pytest -n0 --no-cov src/tests/integration/api/test_global_feed_routes.py
```

**Exit code:** `2` (make: `Error 1`)  
**Counts:** 2 failed, 10 passed (12 collected) in 8.90s

### Failed tests

#### `test_global_feed_cards_and_posts_chronology`

File: `src/tests/integration/api/test_global_feed_routes.py:96`

```
E       AssertionError: assert 'movie_card' == 'feed_post'
E
E         - feed_post
E         + movie_card
```

Snippet:

```python
        kinds = [it['kind'] for it in body['items']]
        assert 'movie_card' in kinds and 'feed_post' in kinds
        card_ids_all = [it['id'] for it in body['items'] if it['kind'] == 'movie_card']
        assert card_id in card_ids_all
        # Пост создан позже — первым в хронологии
>       assert kinds[0] == 'feed_post'
E       AssertionError: assert 'movie_card' == 'feed_post'
```

Test helper `_card_updated_at_before_post(card_id, post_id)` still forces card `updated_at` before the post, but global feed `kind=all` now returns `movie_card` first (sort key is no longer `updated_at` for cards).

#### `test_global_feed_all_does_not_resurface_card_on_rating_patch`

File: `src/tests/integration/api/test_global_feed_routes.py:254`

```
E       AssertionError: assert 'movie_card' == 'feed_post'
E
E         - feed_post
E         + movie_card
```

Snippet:

```python
        before = await async_client.get('/api/feed/global?kind=all&limit=20')
        assert before.status_code == 200
>       assert before.json()['items'][0]['kind'] == 'feed_post'
E       AssertionError: assert 'movie_card' == 'feed_post'
```

Same chronology issue: after creating a card then a newer post, `kind=all` still lists `movie_card` first (before the rating PATCH). The test never reaches the PATCH / no-resurface assertion.

---

## 3. Pytest: movie card feed recommendation

**Command**

```bash
make backend-test-one target=src/tests/integration/api/test_movie_card_feed_recommendation.py
```

Expanded:

```bash
docker exec -w /opt/app filmony-backend uv run pytest -n0 --no-cov src/tests/integration/api/test_movie_card_feed_recommendation.py
```

**Exit code:** `0`  
**Counts:** 8 passed (8 collected) in 7.83s

---

## 4. Pytest: profile routes

**Command**

```bash
make backend-test-one target=src/tests/integration/api/test_profile_routes.py
```

Expanded:

```bash
docker exec -w /opt/app filmony-backend uv run pytest -n0 --no-cov src/tests/integration/api/test_profile_routes.py
```

**Exit code:** `0`  
**Counts:** 46 passed (46 collected) in 31.49s

---

## 5. Pytest: converted planned card promotion

**Command** (`::` node id supported by `make backend-test-one`)

```bash
make backend-test-one target=src/tests/integration/api/test_cards_routes.py::test_movie_card_feed_promotes_converted_planned_card
```

Expanded:

```bash
docker exec -w /opt/app filmony-backend uv run pytest -n0 --no-cov src/tests/integration/api/test_cards_routes.py::test_movie_card_feed_promotes_converted_planned_card
```

**Exit code:** `0`  
**Counts:** 1 passed (1 collected) in 1.24s

---

## Summary

| Step | Command | Exit | Result |
|------|---------|------|--------|
| ruff | `docker compose … exec … ruff check` (8 files) | 0 | pass |
| pytest global feed | `make backend-test-one target=src/tests/integration/api/test_global_feed_routes.py` | 2 | **2 failed**, 10 passed |
| pytest movie card feed | `make backend-test-one target=src/tests/integration/api/test_movie_card_feed_recommendation.py` | 0 | 8 passed |
| pytest profile | `make backend-test-one target=src/tests/integration/api/test_profile_routes.py` | 0 | 46 passed |
| pytest converted planned | `make backend-test-one target=…::test_movie_card_feed_promotes_converted_planned_card` | 0 | 1 passed |

**Totals (pytest):** 65 passed, 2 failed across 67 collected tests.

Failed names:

- `src/tests/integration/api/test_global_feed_routes.py::test_global_feed_cards_and_posts_chronology`
- `src/tests/integration/api/test_global_feed_routes.py::test_global_feed_all_does_not_resurface_card_on_rating_patch`
