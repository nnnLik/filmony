# Profile header text metrics

## Summary

Profile header uses a left-aligned avatar with identity and compact text metrics instead of centered layout and bordered chip grid.

## UX

```
[ Avatar ]   Name + streak badge
             @slug
             5 подписчиков · 9 подписок
             397 оценено · 37 позже · 20 любимые

bio (left-aligned)
[Пригласить угадать] / follow actions
```

- **Own profile** (`/profile`): shared `ProfileHeader`, no taste-quiz badge on name.
- **Public profile** (`/u/:id`): same header with taste-quiz badge when applicable.
- All five metrics remain clickable with the same navigation targets as before.

## Components

| File | Role |
|------|------|
| `ProfileHeader.tsx` | Left avatar row; optional embedded `ProfileCompactMetrics` |
| `ProfileCompactMetrics.tsx` | Two-line text metric strip |
| `ProfilePage.tsx` | Own profile wiring |
| `PublicProfilePage.tsx` | Public profile wiring |

## Verification

```bash
cd frontend && npm run lint && npm run build
```

## Related

- Prior stats work: [profile-stats-people-restructure](./profile-stats-people-restructure.md)
