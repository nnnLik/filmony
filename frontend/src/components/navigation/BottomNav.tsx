import { NavLink } from 'react-router-dom'

function IconFeed({ active }: { active: boolean }) {
  const stroke = active ? 'var(--tgui--link_color, #2481cc)' : 'var(--tgui--hint_color, #8e8e93)'
  return (
    <svg aria-hidden className="size-6" fill="none" viewBox="0 0 24 24" stroke={stroke} strokeWidth={active ? 2.2 : 1.5}>
      <path d="M4 10.5 12 4l8 6.5V20a1 1 0 0 1-1 1h-5v-6H10v6H5a1 1 0 0 1-1-1v-9.5Z" strokeLinejoin="round" />
    </svg>
  )
}

function IconUser({ active }: { active: boolean }) {
  const stroke = active ? 'var(--tgui--link_color, #2481cc)' : 'var(--tgui--hint_color, #8e8e93)'
  return (
    <svg aria-hidden className="size-6" fill="none" viewBox="0 0 24 24" stroke={stroke} strokeWidth={active ? 2.2 : 1.5}>
      <circle cx="12" cy="9" r="3.5" />
      <path d="M6.5 20.2c.7-3.2 3.4-5.2 5.5-5.2s4.8 2 5.5 5.2" strokeLinecap="round" />
    </svg>
  )
}

export function BottomNav() {
  return (
    <nav
      className="fixed bottom-0 left-0 right-0 z-30 border-t border-(--tgui--divider_color, rgba(0,0,0,.08)) bg-(--tgui--bg_color, #fff) pb-[max(0.5rem,env(safe-area-inset-bottom))] shadow-[0_-4px_24px_rgba(0,0,0,.06)] dark:border-white/10 dark:bg-[#212121] dark:shadow-[0_-4px_24px_rgba(0,0,0,.35)]"
      aria-label="Основные разделы"
    >
      <div className="mx-auto flex max-w-md items-stretch justify-around px-6 pt-1">
        <NavLink
          to="/"
          end
          className={({ isActive }) =>
            `flex min-w-18 flex-col items-center gap-0.5 rounded-xl px-6 py-2 text-[11px] font-semibold tracking-tight transition-colors ${
              isActive ? 'text-(--tgui--link_color, #2481cc)' : 'text-(--tgui--hint_color, #8e8e93)'
            }`
          }
        >
          {({ isActive }) => (
            <>
              <IconFeed active={isActive} />
              Лента
            </>
          )}
        </NavLink>
        <NavLink
          to="/profile"
          className={({ isActive }) =>
            `flex min-w-18 flex-col items-center gap-0.5 rounded-xl px-6 py-2 text-[11px] font-semibold tracking-tight transition-colors ${
              isActive ? 'text-(--tgui--link_color, #2481cc)' : 'text-(--tgui--hint_color, #8e8e93)'
            }`
          }
        >
          {({ isActive }) => (
            <>
              <IconUser active={isActive} />
              Профиль
            </>
          )}
        </NavLink>
      </div>
    </nav>
  )
}
