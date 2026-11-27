# Product release feed post — reference

Companion to [SKILL.md](SKILL.md). Rule: [`.cursor/rules/product-release-feed-post.mdc`](../../rules/product-release-feed-post.mdc).

## Voice and structure

- **Language:** Russian
- **Tone:** founder / product — simple, warm, what the **user sees**
- **Grouping:** product areas — **Профиль**, **Фильмы**, **Просмотр**, **Лента**, etc. (use only areas that changed)
- **Bullets:** short lines starting with `•`
- **Open:** one-line hook (e.g. «Обновили приложение ✨»)
- **Close:** short warm sign-off (e.g. «Приятных просмотров 🎬»)
- **Artifact:** пост в ленте / **FeedPost** — not a rated card (`UserCard`)

## Forbidden in post text

Do **not** mention:

| Category | Examples |
|----------|----------|
| Engineering | commits, PRs, branches, merge, deploy pipeline |
| Internal ids | `profile_slug`, UUIDs, `feed_post` id, `completed_at` |
| Stack / ops | API, TTL, Docker, JWT, SQL, Celery, SSE |
| Process | «не закоммичено», «в работе», «скоро», «планируем» |
| Code | file names, component names, heatmap-as-engineering jargon |
| Meta | «мы добавили эндпоинт», «рефакторинг сервиса» |

Write **outcomes**, not implementation.

## Scope gate

- Include **only** changes that are **live on prod** at publish time
- Omit infra-only, CI, healthcheck, and docs-only work
- Omit features still uncommitted or not deployed

## Canonical example (approved structure)

Use this as the template for tone, grouping, and bullet style:

```
Обновили приложение ✨

Профиль
• Теплокарта активности теперь на главном экране — сразу видно, как вы смотрите фильмы
• Статистика разложена по вкладкам: Обзор, Вкус и Сообщество
• Можно сравнить свои оценки с Кинопоиском, IMDb и сообществом

Фильмы
• На странице фильма больше полезного: длительность, возраст, оценки КП и IMDb, трейлер, где смотреть и похожие

Просмотр
• После просмотра спрашиваем, хотите ли оценить фильм
• Если фильм пока нельзя посмотреть — честно об этом говорим
• На карточке фильма видны оценки друзей
• В профиле: фильмы, которые оба хотите посмотреть, «вечер на двоих» и кто из друзей смотрит прямо сейчас
• В Telegram «Смотреть» открывает просмотр в браузере

Приятных просмотров 🎬
```

## Prod publish (API — required path)

**Environment:** SSH alias `homelab` → container `filmony-backend`, workdir `/opt/app`. **Not** local Docker.

**Flow:** resolve `profile_slug` → issue JWT inside container (never print token) → `POST /api/feed-posts` → print only `id` / `created_at` / HTTP status.

**Port:** read `$PORT` from container env (prod may differ from 8000). **Never hardcode 8000.**

### One-shot publish snippet

Replace `BODY` with the approved draft (escape quotes in the heredoc). Default slug `u83128ffb7116` — confirm with user.

```bash
ssh homelab 'docker exec -i -w /opt/app filmony-backend python -' <<'PY'
import asyncio
import json
import os
import urllib.error
import urllib.request

from sqlalchemy import select

from core.database import get_session_factory
from models.user import User
from services.auth.issue_session_jwt import IssueSessionJwtService

SLUG = "u83128ffb7116"
BODY = """Обновили приложение ✨

… approved draft …"""

PORT = os.environ.get("PORT")
if not PORT:
    raise SystemExit("PORT env var is not set in container")

async def main() -> None:
    async with get_session_factory()() as session:
        user_id = (
            await session.execute(select(User.id).where(User.profile_slug == SLUG))
        ).scalar_one()
    token = IssueSessionJwtService().execute(user_id)
    payload = json.dumps(
        {
            "body": BODY,
            "image_url": None,
            "referenced_movie_card_id": None,
            "source_comment_id": None,
        }
    ).encode()
    req = urllib.request.Request(
        f"http://127.0.0.1:{PORT}/api/feed-posts",
        data=payload,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode())
            print(json.dumps({"status": resp.status, "id": data.get("id"), "created_at": data.get("created_at")}))
    except urllib.error.HTTPError as e:
        print(json.dumps({"status": e.code, "error": e.read().decode()[:500]}))

asyncio.run(main())
PY
```

**Success:** HTTP 200, JSON includes `id`, `created_at`. Post appears in global feed and author profile immediately.

**Side effects via API (do not skip):** `CreateFeedPostService`, follower Telegram notify, mention notify, global feed SSE bump.

## SQL fallback (not allowed by default)

Raw `INSERT INTO feed_post` **skips** follower Telegram notifications and `bump_global_feed_head_version()`. Use **only** if `POST /api/feed-posts` is unavailable **and** the user explicitly accepts missing notifications. Prefer fixing API access instead.

## Default announcement account

| Field | Value |
|-------|-------|
| `profile_slug` | `u83128ffb7116` |
| Display name | makhm_ra |

Always confirm slug with the user before publish.
