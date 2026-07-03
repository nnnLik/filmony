# Profile Taste Match — Decision Log

**Status:** blocked — fill before implementation

Each row must move from `TBD` → `DECIDED` with date, owner, and short rationale.

| § | Topic | Decision | Date | Rationale |
|---|-------|----------|------|-----------|
| 1 | Comparison pool | TBD | | |
| 2 | Title identity key | TBD | | |
| 3 | Signal catalog + weights | TBD | | |
| 4 | Scoring formula & normalization | TBD | | |
| 5 | Tag/genre weighting rules | TBD | | |
| 6 | Privacy & breakdown visibility | TBD | | |
| 7 | API shape (extend /stats vs new route) | TBD | | |
| 8 | UI surfaces & copy | TBD | | |
| 9 | Performance & caching | TBD | | |
| 10 | Golden test fixtures | TBD | | |

## Weight table (§3 + §4)

_Publish after decisions — weights must sum to 1.0 per formula version._

| Signal | Weight | Min sample | Included |
|--------|--------|------------|----------|
| | | | |

## Worked examples (§4)

_Three fictional profile pairs with expected score band after formula is chosen._

| Pair | Shared titles | Shared tags | Rating delta | Expected band |
|------|---------------|-------------|--------------|---------------|
| | | | | |

## Sign-off

- [ ] Product / design approved formula and UI copy
- [ ] Backend approved performance approach
- [ ] Ready to create `plan.md` implementation steps
