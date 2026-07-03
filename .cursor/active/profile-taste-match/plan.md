# Profile Taste Match — Plan

**Status:** blocked on `.cursor/active/profile-taste-match/decisions.md`

Do **not** implement until all §1–§10 in `.cursor/features/profile-taste-match/feature.md` are resolved.

## After decisions are locked

1. Backend: `ComputeProfileTasteMatchService` + `RankProfileTastePeersService` per approved formula.
2. API: extend `/stats` social block and/or add pairwise route per §7.
3. Tests: golden fixtures from §10 in `backend/src/tests/`.
4. Frontend: upgrade `SocialTastePeers`, optional public profile match badge.
5. Docs: `docs/features/profile-taste-match.md`, update `profile-analytics-redesign` cross-link.
