# Result: profile-header-text-metrics

Status: `completed`

## Implemented

- Replaced centered avatar + bordered metric chips with left-aligned `ProfileHeader` row (avatar ~76px, identity block on the right).
- Rewrote `ProfileCompactMetrics` as two tappable text lines: social (подписчиков · подписок) and library (оценено · позже · любимые).
- Unified own (`ProfilePage`) and public (`PublicProfilePage`) profiles on shared header with embedded metrics.
- Left-aligned bio, invite button, and public follow actions.

## Changed files

- `frontend/src/components/profile/ProfileCompactMetrics.tsx`
- `frontend/src/components/profile/ProfileHeader.tsx`
- `frontend/src/pages/ProfilePage.tsx`
- `frontend/src/pages/PublicProfilePage.tsx`
- `.cursor/features/profile-header-text-metrics/feature.md`
- `.cursor/active/profile-header-text-metrics/plan.md`
- `.cursor/active/profile-header-text-metrics/progress.md`
- `docs/features/profile-header-text-metrics.md`

## Verification

- `cd frontend && npm run lint` — pass
- `cd frontend && npm run build` — pass

## Known limitations

- Russian plural labels are static (e.g. «5 подписчиков» for all counts); no declension by number.
- Recap banner and export messages remain centered where they were before.

## Next steps

- Optional: declension helper for follower/following labels.
- Optional: align export/recap blocks to left for full visual consistency.
