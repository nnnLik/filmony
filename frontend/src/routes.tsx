import { Route, Routes } from 'react-router-dom'

import { AppShell } from './layout/AppShell'
import { FeedPage } from './pages/FeedPage'
import { ProfilePage } from './pages/ProfilePage'
import { PublicProfilePage } from './pages/PublicProfilePage'

export function AppRoutes() {
  return (
    <Routes>
      <Route path="/" element={<AppShell />}>
        <Route index element={<FeedPage />} />
        <Route path="profile" element={<ProfilePage />} />
      </Route>
      <Route path="/u/:identifier" element={<PublicProfilePage />} />
    </Routes>
  )
}
