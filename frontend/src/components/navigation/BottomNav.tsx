import { Home, Search, User } from 'lucide-react'
import type { ReactNode } from 'react'
import { NavLink } from 'react-router'

function NavIcon({
  active,
  children,
}: {
  active: boolean
  children: ReactNode
}) {
  return (
    <span
      className="block transition-[stroke,transform] duration-200 ease-out [&>svg]:block [&>svg]:size-[22px]"
      style={{ transform: active ? 'scale(1.05)' : 'scale(1)' }}
    >
      {children}
    </span>
  )
}

const itemBase =
  'group relative flex min-h-[52px] min-w-0 flex-1 flex-col items-center justify-center gap-0.5 rounded-2xl px-3 py-2 text-[11px] font-semibold tracking-tight no-underline transition-[color,background,box-shadow] duration-200 ease-out outline-none focus-visible:ring-2 focus-visible:ring-[color-mix(in_srgb,var(--filmony-mint,#5eead4)_55%,transparent)] focus-visible:ring-offset-2 focus-visible:ring-offset-[var(--filmony-void,#0a1018)]'

export function BottomNav() {
  return (
    <div className="pointer-events-none fixed inset-x-0 bottom-0 z-30 flex justify-center px-3 pb-[max(10px,calc(8px+env(safe-area-inset-bottom)))] pt-2">
      <nav
        className="pointer-events-auto relative w-full max-w-md overflow-hidden rounded-[26px] border border-[color-mix(in_srgb,var(--filmony-mint,#5eead4)_18%,transparent)] bg-[color-mix(in_srgb,var(--filmony-surface,#111b27)_78%,transparent)] px-1.5 py-1.5 shadow-[0_12px_48px_rgba(0,0,0,.45),0_0_0_1px_rgba(94,234,212,.06),inset_0_1px_0_rgba(255,255,255,.04)] backdrop-blur-2xl backdrop-saturate-150"
        style={{ WebkitBackdropFilter: 'blur(24px) saturate(1.4)' }}
        aria-label="Основные разделы"
      >
        <div
          className="pointer-events-none absolute inset-x-8 top-0 h-px bg-gradient-to-r from-transparent via-[color-mix(in_srgb,var(--filmony-mint,#5eead4)_35%,transparent)] to-transparent opacity-80"
          aria-hidden
        />
        <div className="relative flex items-stretch gap-0.5">
          <NavLink
            to="/"
            end
            className={({ isActive }) =>
              `${itemBase} ${isActive ? 'text-[var(--filmony-mint,#5eead4)]' : 'text-[var(--filmony-muted,#7f95ab)]'}`
            }
          >
            {({ isActive }) => (
              <>
                {isActive ? (
                  <span
                    className="absolute inset-0 rounded-2xl bg-[color-mix(in_srgb,var(--filmony-mint,#5eead4)_14%,transparent)] shadow-[inset_0_0_0_1px_color-mix(in_srgb,var(--filmony-mint,#5eead4)_22%,transparent)]"
                    aria-hidden
                  />
                ) : null}
                <span className="relative z-[1] flex flex-col items-center gap-0.5">
                  <NavIcon active={isActive}>
                    <Home aria-hidden strokeWidth={isActive ? 2.25 : 1.55} />
                  </NavIcon>
                  Лента
                </span>
              </>
            )}
          </NavLink>
          <NavLink
            to="/search"
            className={({ isActive }) =>
              `${itemBase} ${isActive ? 'text-[var(--filmony-mint,#5eead4)]' : 'text-[var(--filmony-muted,#7f95ab)]'}`
            }
          >
            {({ isActive }) => (
              <>
                {isActive ? (
                  <span
                    className="absolute inset-0 rounded-2xl bg-[color-mix(in_srgb,var(--filmony-mint,#5eead4)_14%,transparent)] shadow-[inset_0_0_0_1px_color-mix(in_srgb,var(--filmony-mint,#5eead4)_22%,transparent)]"
                    aria-hidden
                  />
                ) : null}
                <span className="relative z-[1] flex flex-col items-center gap-0.5">
                  <NavIcon active={isActive}>
                    <Search aria-hidden strokeWidth={isActive ? 2.35 : 1.65} />
                  </NavIcon>
                  Поиск
                </span>
              </>
            )}
          </NavLink>
          <NavLink
            to="/profile"
            className={({ isActive }) =>
              `${itemBase} ${isActive ? 'text-[var(--filmony-amber,#e8b86d)]' : 'text-[var(--filmony-muted,#7f95ab)]'}`
            }
          >
            {({ isActive }) => (
              <>
                {isActive ? (
                  <span
                    className="absolute inset-0 rounded-2xl bg-[color-mix(in_srgb,var(--filmony-amber,#e8b86d)_16%,transparent)] shadow-[inset_0_0_0_1px_color-mix(in_srgb,var(--filmony-amber,#e8b86d)_28%,transparent)]"
                    aria-hidden
                  />
                ) : null}
                <span className="relative z-[1] flex flex-col items-center gap-0.5">
                  <NavIcon active={isActive}>
                    <User aria-hidden strokeWidth={isActive ? 2.25 : 1.55} />
                  </NavIcon>
                  Профиль
                </span>
              </>
            )}
          </NavLink>
        </div>
      </nav>
    </div>
  )
}
