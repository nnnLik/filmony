import { lazy, Suspense } from 'react'
import { Route, Routes } from 'react-router-dom'

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

export function AppRoutes() {
  return (
    <Suspense fallback={<RoutePageFallback />}>
      <Routes>
        <Route path="/" element={<AppShell />}>
          <Route index element={<FeedPage />} />
          <Route path="search" element={<SearchPage />} />
          <Route path="cards/new" element={<CreateCardPage />} />
          <Route path="profile" element={<ProfilePage />} />
          <Route path="profile/edit" element={<ProfileEditPage />} />
          <Route path="profile/subscriptions" element={<SubscriptionsPage />} />
        </Route>
        <Route path="/u/:userId" element={<PublicProfilePage />} />
        <Route path="/u/:userId/subscriptions" element={<SubscriptionsPage />} />
        <Route path="/films/:filmId" element={<FilmDetailPage />} />
        <Route path="/feed-posts/:postId" element={<FeedPostDetailPage />} />
        <Route path="/cards/:cardId" element={<MovieCardDetailPage />} />
        <Route path="/cards/:cardId/share" element={<ShareMovieCardPage />} />
        <Route path="/cards/:cardId/edit" element={<EditMovieCardPage />} />
        <Route path="/cards/:cardId/edit-planned" element={<CreateCardPage />} />
      </Routes>
    </Suspense>
  )
}
