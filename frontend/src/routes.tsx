import { Route, Routes } from 'react-router-dom'

import { AppShell } from './layout/AppShell'
import { CreateCardPage } from './pages/CreateCardPage'
import { FeedPage } from './pages/FeedPage'
import { ProfileEditPage } from './pages/ProfileEditPage'
import { ProfilePage } from './pages/ProfilePage'
import { PublicProfilePage } from './pages/PublicProfilePage'

export function AppRoutes() {
  return (
    <Routes>
      <Route path="/" element={<AppShell />}>
        <Route index element={<FeedPage />} />
        <Route path="cards/new" element={<CreateCardPage />} />
        <Route path="profile" element={<ProfilePage />} />
        <Route path="profile/edit" element={<ProfileEditPage />} />
      </Route>
      <Route path="/u/:identifier" element={<PublicProfilePage />} />
    </Routes>
  )
}
