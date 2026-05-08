import { Route, Routes } from 'react-router-dom'

import { AppShell } from './layout/AppShell'
import { CreateCardPage } from './pages/CreateCardPage'
import { EditMovieCardPage } from './pages/EditMovieCardPage'
import { FeedPage } from './pages/FeedPage'
import { FilmDetailPage } from './pages/FilmDetailPage'
import { MovieCardDetailPage } from './pages/MovieCardDetailPage'
import { ShareMovieCardPage } from './pages/ShareMovieCardPage'
import { ProfileEditPage } from './pages/ProfileEditPage'
import { ProfilePage } from './pages/ProfilePage'
import { PublicProfilePage } from './pages/PublicProfilePage'
import { SubscriptionsPage } from './pages/SubscriptionsPage'

export function AppRoutes() {
  return (
    <Routes>
      <Route path="/" element={<AppShell />}>
        <Route index element={<FeedPage />} />
        <Route path="cards/new" element={<CreateCardPage />} />
        <Route path="profile" element={<ProfilePage />} />
        <Route path="profile/edit" element={<ProfileEditPage />} />
        <Route path="profile/subscriptions" element={<SubscriptionsPage />} />
      </Route>
      <Route path="/u/:userId" element={<PublicProfilePage />} />
      <Route path="/u/:userId/subscriptions" element={<SubscriptionsPage />} />
      <Route path="/films/:filmId" element={<FilmDetailPage />} />
      <Route path="/cards/:cardId" element={<MovieCardDetailPage />} />
      <Route path="/cards/:cardId/share" element={<ShareMovieCardPage />} />
      <Route path="/cards/:cardId/edit" element={<EditMovieCardPage />} />
    </Routes>
  )
}
