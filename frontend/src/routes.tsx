import { lazy, Suspense } from 'react'
import { Route, Routes } from 'react-router'

import { AppShell } from './layout/AppShell'
import { RoutePageFallback } from './layout/RoutePageFallback'

const FeedPage = lazy(async () => {
  const m = await import('./pages/FeedPage')
  return { default: m.FeedPage }
})
const SearchPage = lazy(async () => {
  const m = await import('./pages/SearchPage')
  return { default: m.SearchPage }
})
const CreateCardPage = lazy(async () => {
  const m = await import('./pages/CreateCardPage')
  return { default: m.CreateCardPage }
})
const ProfilePage = lazy(async () => {
  const m = await import('./pages/ProfilePage')
  return { default: m.ProfilePage }
})
const ProfileEditPage = lazy(async () => {
  const m = await import('./pages/ProfileEditPage')
  return { default: m.ProfileEditPage }
})
const SubscriptionsPage = lazy(async () => {
  const m = await import('./pages/SubscriptionsPage')
  return { default: m.SubscriptionsPage }
})
const PublicProfilePage = lazy(async () => {
  const m = await import('./pages/PublicProfilePage')
  return { default: m.PublicProfilePage }
})
const FilmDetailPage = lazy(async () => {
  const m = await import('./pages/FilmDetailPage')
  return { default: m.FilmDetailPage }
})
const DirectorDetailPage = lazy(async () => {
  const m = await import('./pages/DirectorDetailPage')
  return { default: m.DirectorDetailPage }
})
const DirectorsIndexPage = lazy(async () => {
  const m = await import('./pages/DirectorsIndexPage')
  return { default: m.DirectorsIndexPage }
})
const FranchiseDetailPage = lazy(async () => {
  const m = await import('./pages/FranchiseDetailPage')
  return { default: m.FranchiseDetailPage }
})
const GenresIndexPage = lazy(async () => {
  const m = await import('./pages/GenresIndexPage')
  return { default: m.GenresIndexPage }
})
const GenreDetailPage = lazy(async () => {
  const m = await import('./pages/GenreDetailPage')
  return { default: m.GenreDetailPage }
})
const CatalogDetailPage = lazy(async () => {
  const m = await import('./pages/CatalogDetailPage')
  return { default: m.CatalogDetailPage }
})
const FeedPostDetailPage = lazy(async () => {
  const m = await import('./pages/FeedPostDetailPage')
  return { default: m.FeedPostDetailPage }
})
const MovieCardDetailPage = lazy(async () => {
  const m = await import('./pages/MovieCardDetailPage')
  return { default: m.MovieCardDetailPage }
})
const ShareMovieCardPage = lazy(async () => {
  const m = await import('./pages/ShareMovieCardPage')
  return { default: m.ShareMovieCardPage }
})
const EditMovieCardPage = lazy(async () => {
  const m = await import('./pages/EditMovieCardPage')
  return { default: m.EditMovieCardPage }
})
const CreateWatchlistPage = lazy(async () => {
  const m = await import('./pages/CreateWatchlistPage')
  return { default: m.CreateWatchlistPage }
})
const EditPlannedWatchlistPage = lazy(async () => {
  const m = await import('./pages/CreateWatchlistPage')
  return { default: m.EditPlannedWatchlistPage }
})
const TasteQuizPlayPage = lazy(async () => {
  const m = await import('./pages/TasteQuizPlayPage')
  return { default: m.TasteQuizPlayPage }
})
const TasteQuizInvitePage = lazy(async () => {
  const m = await import('./pages/TasteQuizInvitePage')
  return { default: m.TasteQuizInvitePage }
})
const TasteQuizInviteLandingPage = lazy(async () => {
  const m = await import('./pages/TasteQuizInviteLandingPage')
  return { default: m.TasteQuizInviteLandingPage }
})
const TasteQuizStatsPage = lazy(async () => {
  const m = await import('./pages/TasteQuizStatsPage')
  return { default: m.TasteQuizStatsPage }
})
const MonthlyRecapPage = lazy(async () => {
  const m = await import('./pages/MonthlyRecapPage')
  return { default: m.MonthlyRecapPage }
})
const CollectionDetailPage = lazy(async () => {
  const m = await import('./pages/CollectionDetailPage')
  return { default: m.CollectionDetailPage }
})
const CollectionsIndexPage = lazy(async () => {
  const m = await import('./pages/CollectionsIndexPage')
  return { default: m.CollectionsIndexPage }
})

export function AppRoutes() {
  return (
    <Suspense fallback={<RoutePageFallback />}>
      <Routes>
        <Route path="/" element={<AppShell />}>
          <Route index element={<FeedPage />} />
          <Route path="search" element={<SearchPage />} />
          <Route path="collections" element={<CollectionsIndexPage />} />
          <Route path="collections/:slug" element={<CollectionDetailPage />} />
          <Route path="cards/new" element={<CreateCardPage />} />
          <Route path="watchlist/new" element={<CreateWatchlistPage />} />
          <Route path="profile" element={<ProfilePage />} />
          <Route path="profile/edit" element={<ProfileEditPage />} />
          <Route path="profile/subscriptions" element={<SubscriptionsPage />} />
        </Route>
        <Route path="/u/:userId" element={<PublicProfilePage />} />
        <Route path="/u/:userId/subscriptions" element={<SubscriptionsPage />} />
        <Route path="/films/:filmId" element={<FilmDetailPage />} />
        <Route path="/directors" element={<DirectorsIndexPage />} />
        <Route path="/directors/:kinopoiskId" element={<DirectorDetailPage />} />
        <Route path="/franchises/:franchiseKey" element={<FranchiseDetailPage />} />
        <Route path="/genres" element={<GenresIndexPage />} />
        <Route path="/genres/:slug" element={<GenreDetailPage />} />
        <Route path="/catalog/:catalogItemId" element={<CatalogDetailPage />} />
        <Route path="/games/:catalogItemId" element={<CatalogDetailPage />} />
        <Route path="/feed-posts/:postId" element={<FeedPostDetailPage />} />
        <Route path="/cards/:cardId" element={<MovieCardDetailPage />} />
        <Route path="/cards/:cardId/share" element={<ShareMovieCardPage />} />
        <Route path="/cards/:cardId/edit" element={<EditMovieCardPage />} />
        <Route path="/cards/:cardId/edit-planned" element={<EditPlannedWatchlistPage />} />
        <Route path="/taste-quiz/play/:ownerId" element={<TasteQuizPlayPage />} />
        <Route path="/taste-quiz/invite/:inviteToken" element={<TasteQuizInviteLandingPage />} />
        <Route path="/taste-quiz/invite" element={<TasteQuizInvitePage />} />
        <Route path="/taste-quiz/stats" element={<TasteQuizStatsPage />} />
        <Route path="/me/recap/:year/:month" element={<MonthlyRecapPage />} />
        <Route path="/me/recap/latest" element={<MonthlyRecapPage />} />
      </Routes>
    </Suspense>
  )
}
