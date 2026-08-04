# Feature: Frontend Refactor + UX Polish Pack

## Scope

Комплексный рефакторинг frontend-компонентов и UX-полировка:

- UI-примитивы (PageLoadingState, skeletons, StickyBackHeader)
- Comment thread extraction (hooks + shared components)
- Catalog/profile/card form deduplication
- Feed explainability («Для вас» tab), offline banner, search debounce
- Social polish (friends rated, watchlist overlap)
- Game pages parity

## Acceptance criteria

- [x] Shared loading/error/empty states on catalog, profile, search, taste quiz pages
- [x] Comment thread shared across FeedCard, FeedPostCard, detail pages
- [x] Catalog index/detail pages use shared layout components
- [x] ProfilePage/PublicProfilePage share tab panels
- [x] Card form fields deduplicated between create/edit
- [x] Offline feed banner заметнее
- [x] Skeletons on detail/catalog/profile/search pages
- [x] Feed «Для вас» tab with explainability chips
- [x] Director/franchise empty states with CTA
- [x] Catalog search debounce 400ms + skeleton
- [x] FollowingRatingsPanel polish + friends-first filter
- [x] CatalogDetailPage watchlist parity + game route alias
- [x] useGlobalFeed hook extracted from FeedPage
- [x] `npm run lint && npm run build` pass
