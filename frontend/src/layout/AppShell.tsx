import { Outlet } from 'react-router-dom'

import { BottomNav } from '../components/navigation/BottomNav'

export function AppShell() {
  return (
    <div className="flex min-h-dvh flex-col bg-(--tgui--bg_color) text-(--tgui--text_color)">
      <div className="mx-auto w-full max-w-md flex-1 pb-[calc(5.75rem+env(safe-area-inset-bottom))]">
        <Outlet />
      </div>
      <BottomNav />
    </div>
  )
}
