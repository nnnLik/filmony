# Personal digest redesign — progress

**Feature slug:** `personal-digest-redesign`  
**Status:** Phase 3 complete (fun facts engine)

## Phase 3 (2026-08-08)

- [x] `BuildPersonalDigestFunFactsService` with 9 rule plugins + microFun fallback pools
- [x] Wired fun facts into `BuildMonthlyRecapService` and weekly path in `BuildPersonalDigestService`
- [x] Exported from `services/personal_digest/__init__.py`
- [x] Unit tests `test_fun_facts.py`
- [x] Deprecated note on `tasks/monthly_recap.py`
- [x] Docs: `docs/features/personal-digest-redesign.md`, updated `monthly-recap.md`
- [x] Frontend: `digest_weekly` / `digest_monthly` pools; fun facts on `MonthlyRecapPage`

## Verification

```bash
make backend-test-one target=src/tests/unit/services/personal_digest/
make backend-test-one target=src/tests/integration/services/personal_digest/
cd frontend && npm run lint && npm run build
```
