# Personal digest redesign — Phase 3 result

**Date:** 2026-08-08  
**Status:** Phase 3 complete

## Implemented

- Rule-based fun facts engine (`BuildPersonalDigestFunFactsService`) with scored plugins: `genre_dominance`, `rating_all_high`, `rating_wide_spread`, `era_skew`, `collection_sprint`, `marathon_complete`, `new_country_burst`, `streak_record`, `microfun_fallback`
- Top K selection: weekly=3, monthly=5; deterministic tie-break via `user_id + period_key`
- MicroFun fallback pools `digest_weekly` / `digest_monthly` (backend + frontend mirror)
- Fun facts wired into monthly recap and weekly digest builders
- Deprecation note on legacy `tasks/monthly_recap.py`

## Changed files

| Area | Files |
|------|-------|
| Backend service | `backend/src/services/personal_digest/build_personal_digest_fun_facts.py` (new) |
| Wiring | `backend/src/services/profile/build_monthly_recap.py`, `backend/src/services/personal_digest/build_personal_digest.py`, `backend/src/services/personal_digest/__init__.py` |
| Tests | `backend/src/tests/unit/services/personal_digest/test_fun_facts.py` (new) |
| Tasks | `backend/src/tasks/monthly_recap.py` |
| Docs | `docs/features/personal-digest-redesign.md` (new), `docs/features/monthly-recap.md` |
| Frontend | `frontend/src/lib/microFun/microFunCopy.ts`, `frontend/src/pages/MonthlyRecapPage.tsx` |
| Artifacts | `.cursor/active/personal-digest-redesign/progress.md`, `result.md` |

## Verification (2026-08-08)

```bash
make backend-test-one target=src/tests/unit/services/personal_digest/
# 22 passed

make backend-test-one target=src/tests/integration/services/personal_digest/
# 4 passed

cd frontend && npm run lint && npm run build
# OK
```

## Known limitations

- `collection_sprint` requires collection film totals; collections without totals in DB are skipped
- Monthly recap legacy route and digest route share recap aggregation; weekly fun facts computed in digest builder only

## Next steps

- Profile banner unread digest prompts (spec §12)
- Optional opt-out UI (v2)
