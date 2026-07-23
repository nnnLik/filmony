# Comment edit and delete

Authors can edit or delete their own comments on feed posts and user cards.

## API

### Feed post comments

| Method | Path | Auth | Body |
|--------|------|------|------|
| `PATCH` | `/api/feed-posts/{post_id}/comments/{comment_id}` | Author | `{ "text": string }` (1–250) |
| `DELETE` | `/api/feed-posts/{post_id}/comments/{comment_id}` | Author | — |

- `403` if not the comment author.
- `404` if comment missing or `comment_id` does not belong to `post_id`.
- Delete is **hard delete**; replies cascade via DB FK.

### User card comments

| Method | Path | Auth | Body |
|--------|------|------|------|
| `PATCH` | `/api/cards/{card_id}/comments/{comment_id}` | Author | `{ "text": string, "image_url"?: string \| null }` — same rule as create: text or image required |
| `DELETE` | `/api/cards/{card_id}/comments/{comment_id}` | Author | — |

Same status codes and delete semantics as feed post comments.

## Services

- `UpdateFeedPostCommentService`, `DeleteFeedPostCommentService`
- `UpdateUserCardCommentService`, `DeleteUserCardCommentService`

Text validation reuses reaction-token and mention rules from create flows.

## Frontend

On **post detail** and **card detail**, the comment author sees **Изменить** / **Удалить** next to **Ответить**. Edit opens an inline textarea; delete asks for confirmation and reloads the thread.

## Tests

```bash
make backend-test-one target='src/tests/api/test_feed_posts_routes.py::test_feed_post_comment_update_and_delete'
make backend-test-one target='src/tests/api/test_cards_routes.py::test_user_card_comment_update_and_delete'
```
