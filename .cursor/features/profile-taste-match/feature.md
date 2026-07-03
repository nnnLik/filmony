# Weighted Taste Match (profile-taste-match)

## Metadata
- Feature slug: `profile-taste-match`
- Title: Weighted Taste Match Between Profiles
- Status: **planned — blocked on product decisions below**
- Author: `r.makkhmudov`
- Created at: `2026-06-30`
- Updated at: `2026-07-03`
- Priority: high (follow-up to `profile-analytics-redesign`)
- Target area: backend + frontend

## Problem Statement

После `profile-analytics-redesign` блок «Похожие профили» в статистике использует **простой Jaccard по общим `film_id`** среди подписчиков/подписок (`GetUserProfileSocialInsightsService`). Это даёт понятный v1, но:

- не учитывает **теги, жанры, близость оценок, избранное**;
- плохо работает при **разном размере коллекций** (300 vs 9 карточек);
- **игнорирует не-film карточки** (games / `catalog_item`);
- процент similarity **трудно интерпретировать** без объяснения состава score.

Нужна отдельная фича: **взвешенная модель taste match**, с заранее зафиксированными правилами до написания кода.

## Relationship to existing work

| Already shipped (v1) | This feature (v2) |
|----------------------|-------------------|
| `GET /api/users/:id/stats` → `social.taste_peers[]` | Replace or extend ranking formula |
| Jaccard: `shared / union` on `film_id` | Weighted composite score |
| Top 5 from followers ∪ following | Same pool or wider (TBD) |
| UI: `SocialTastePeers` in stats tab | Richer breakdown + optional compare-on-public-profile |

**Non-goal for v1 replacement day-one:** ломать контракт `/stats` без migration plan — только additive fields or versioned score.

## Goals

- Дать пользователю **осмысленный** процент/уровень совпадения вкуса с другим профилем.
- Показать **почему** совпадение высокое (общие фильмы, теги, близкие оценки).
- Сохранить **детерминизм, тестируемость, кэшируемость**.
- Не раскрывать приватные данные сверх уже публичного профиля.

## Non-Goals

- ML / embeddings / offline training.
- Рекомендательная лента «кого подписаться» (может переиспользовать score позже).
- Сравнение с пользователями вне сети подписок (unless explicitly decided in §1).
- Real-time пересчёт при каждом PATCH карточки без кэша/материализации.

---

## ⚠️ Pre-implementation decisions (MUST resolve before coding)

Implementation **must not start** until every subsection below has an explicit **Decision** + **Rationale** recorded in `.cursor/active/profile-taste-match/decisions.md` (or appended to this file under *Resolved decisions*).

### 1. Who can be compared with whom?

| Option | Description |
|--------|-------------|
| A | Only followers ∪ following of profile owner (current v1 pool) |
| B | Any two profiles viewer can open (pairwise on demand) |
| C | Viewer ↔ opened profile only (most common UX) |
| D | Owner's network + top global matches (discovery) |

**Questions:**
- Нужен ли отдельный endpoint `GET /users/{a}/taste-match/{b}` или расширяем `/stats`?
- Может ли **неавторизованный** viewer видеть match score?

**Decision:** _TBD_

---

### 2. Identity key for "same title" overlap

Cards may bind via `film_id`, `catalog_item_id`, or `no_provider`.

| Signal | Pros | Cons |
|--------|------|------|
| `film_id` only | Simple, already in v1 | Misses games / custom cards |
| `catalog_item_id` when present, else `film_id` | Closer to universal cards | Mixed join logic |
| Normalized `(provider, external_id)` | Provider-accurate | Harder for manual titles |
| `display_title` fuzzy match | Catches duplicates | False positives |

**Questions:**
- Входят ли **planned** (`is_planned=true`) карточки в overlap? (v1 stats: **нет**)
- Входят ли **watchlist** / **favorites** как отдельные сигналы или только rated cards?

**Decision:** _TBD_

---

### 3. Signal catalog (what enters the score)

Candidate signals — each needs **include y/n**, **weight**, **min sample size**:

| Signal | Example | Notes |
|--------|---------|-------|
| **S1** Shared rated titles | count / Jaccard on identity key | v1 baseline |
| **S2** Tag overlap | weighted by tag frequency or IDF | custom tags are sparse/noisy |
| **S3** Genre overlap | from `film_genres` | only film-backed |
| **S4** Rating agreement | avg abs delta on shared titles | needs ≥ N shared |
| **S5** Rating correlation | Pearson on shared 1–10 | unstable if N < 5 |
| **S6** Favorites overlap | shared `is_favorite` titles | strong taste signal |
| **S7** Shelf / category overlap | same `category_id` names | weak semantic signal |
| **S8** Mood / company pattern | distribution similarity | lifestyle, not title overlap |
| **S9** Activity pattern | heatmap correlation | optional, expensive |

**Questions:**
- Какие сигналы **обязательны для v2**, какие **nice-to-have**?
- Есть ли **cap** на вклад одного сигнала (e.g. tags ≤ 30% of total)?

**Decision:** _TBD — publish weight table summing to 1.0_

---

### 4. Scoring formula

Example composite (illustrative only — **not approved**):

```
score = w1 * jaccard_titles
      + w2 * tag_overlap_coefficient
      + w3 * rating_agreement
      + w4 * favorites_jaccard
```

**Questions:**
- **Linear weighted sum** vs **multiplicative** (penalize weak dimensions)?
- Output range: `0..1`, `0..100`, or **discrete bands** (Низкое / Среднее / Высокое)?
- **Minimum data threshold:** below N rated cards → `insufficient_data` instead of fake 0%?
- **Sparse profile handling:** user with 2 cards vs 300 — normalize how?

**Normalization options (pick one per signal):**
- Raw Jaccard
- Jaccard with **sqrt dampening** on collection size
- **Bayesian shrinkage** toward global mean
- **Percentile** within viewer's network only

**Decision:** _TBD — include worked examples with 3 fake profiles_

---

### 5. Tag & genre weighting specifics

If tags/genres included:

| Question | Options |
|----------|---------|
| Tag match rule | exact string / casefold / stemming |
| Tag weight | uniform / `min(count_a, count_b)` / IDF across corpus |
| Stop tags | exclude `kp-import` and other meta tags? |
| Genre source | `film_genres` only vs user tags as genre proxy |
| Multi-tag card | all tags count or top-K only |

**Decision:** _TBD_

---

### 6. Privacy & visibility

| Data | Public profile today | Allowed in match breakdown? |
|------|---------------------|----------------------------|
| Rated cards list | yes (paginated) | yes |
| Exact ratings on shared titles | yes on card | show side-by-side? |
| Tags | yes | yes |
| Watchlist | yes | only if explicitly in scope |
| Non-shared titles | N/A | **must not leak** |

**Questions:**
- Показывать ли **список общих фильмов** в UI match card?
- Показывать ли **расхождение оценок** («ты 9, он 4») — может быть socially sensitive?

**Decision:** _TBD_

---

### 7. API shape

**Option A — extend `/stats` (social.taste_peers):**
```json
{
  "similarity_score": 0.72,
  "similarity_version": 2,
  "signals": {
    "shared_titles": 12,
    "tag_overlap": 0.41,
    "rating_agreement": 0.88
  },
  "shared_highlights": [...]
}
```

**Option B — dedicated pairwise endpoint:**
`GET /api/users/{target_id}/taste-match?with={other_id}`

**Option C — both:** batch peers in `/stats`, pairwise on profile header.

**Questions:**
- Version field for formula changes?
- Cache TTL / materialized table per `(user_a, user_b)`?
- Max peers to compute per request (performance)?

**Decision:** _TBD_

---

### 8. UI/UX placement

| Surface | Purpose |
|---------|---------|
| Stats → Социальность → «Похожие профили» | upgrade existing list |
| Public profile header | «Ваш taste match: 78%» when viewer ≠ owner |
| Subscriptions list | optional badge per user |
| Compare modal | drill-down with signal breakdown |

**Questions:**
- Primary **one-line explanation** under score (Russian copy)?
- Empty state copy when `< min cards`?
- Tap peer → profile only, or open **compare sheet**?

**Decision:** _TBD — attach wireframe or bullet layout_

---

### 9. Performance & caching

- v1 peer query: one GROUP BY over network — cheap.
- Weighted v2 may need tag joins, genre arrays, rating pairs.

**Questions:**
- Acceptable p95 latency budget on `/stats`?
- Precompute nightly vs on-demand?
- Invalidate on: new card, rating change, tag edit, subscription change?

**Decision:** _TBD_

---

### 10. Testing & acceptance thresholds

Before merge, define **golden fixtures** (3–5 profile pairs) with **expected score ± epsilon**.

Example scenarios to specify expected ordering:
- A vs B: 10 shared films, similar ratings → **high**
- A vs C: 2 shared, divergent ratings → **low**
- A vs D: 0 shared but many shared tags → **medium?** (depends on §3)
- Sparse new user → **insufficient_data**

**Decision:** _TBD — table of fixtures in test plan_

---

## Proposed implementation phases (after decisions locked)

### Phase 0 — Decisions doc
- Fill `.cursor/active/profile-taste-match/decisions.md` with resolved §1–§10.
- Product sign-off on formula + UI copy.

### Phase 1 — Backend core
- `ComputeProfileTasteMatchService` (pairwise).
- `RankProfileTastePeersService` (batch for `/stats`).
- Typed DTOs + `similarity_version`.
- pytest golden fixtures.

### Phase 2 — API
- Extend or add routes per §7.
- Backward compatible: keep v1 `similarity_score` or alias.

### Phase 3 — Frontend
- Upgrade `SocialTastePeers` + optional public profile badge.
- Signal breakdown component.
- Empty / insufficient states.

### Phase 4 — Docs & rollout
- `docs/features/profile-taste-match.md`
- Feature flag or gradual `similarity_version` display.

---

## Acceptance Criteria (final — after decisions)

- [ ] All §1–§10 decisions documented and approved.
- [ ] Weighted score is **deterministic** for same inputs + formula version.
- [ ] Pairwise and/or batch endpoints covered by pytest (happy, sparse, empty, privacy).
- [ ] UI shows score **and** human-readable breakdown per §8.
- [ ] No leakage of non-public titles/ratings beyond existing profile rules.
- [ ] Documented formula with examples in `docs/features/profile-taste-match.md`.
- [ ] Regression: v1 heatmap/stats tab still works if `/stats` contract extended additively.

---

## References

- v1 social insights: `backend/src/services/profile/get_user_profile_social_insights.py`
- v1 stats extension: `docs/features/profile-analytics-redesign.md`
- UI peers list: `frontend/src/components/profile/ProfileStatsCharts.tsx` (`SocialTastePeers`)
- Related search overlap pattern: `backend/src/services/search/search_user_suggestions.py` (`_mutual_circle`)
- Subscriptions: `backend/src/services/subscriptions/list_user_subscriptions.py`
- Following ratings on card: tests in `backend/src/tests/api/test_following_ratings_for_movie_card.py`

## Open questions for product owner

1. Главный сценарий: **«насколько я похож на этого человека»** или **«кого из подписок показать в топе»**?
2. Насколько агрессивно показывать **расхождение оценок** на общих фильмах?
3. Нужен ли taste match **только внутри подписок** или на любом публичном профиле?
