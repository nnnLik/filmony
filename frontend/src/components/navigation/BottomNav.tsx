import { Search } from 'lucide-react'
import { NavLink } from 'react-router-dom'

function IconFeed({ active }: { active: boolean }) {
  return (
    <svg
      aria-hidden
      className="size-[22px] transition-[stroke,transform] duration-200 ease-out"
      fill="none"
      viewBox="0 0 24 24"
      stroke="currentColor"
      strokeWidth={active ? 2.25 : 1.55}
      style={{ transform: active ? 'scale(1.05)' : 'scale(1)' }}
    >
      <path d="M4 10.5 12 4l8 6.5V20a1 1 0 0 1-1 1h-5v-6H10v6H5a1 1 0 0 1-1-1v-9.5Z" strokeLinejoin="round" />
    </svg>
  )
}

function IconSearch({ active }: { active: boolean }) {
  return (
    <Search
      aria-hidden
      className="size-[22px] transition-[stroke,transform] duration-200 ease-out"
      strokeWidth={active ? 2.35 : 1.65}
      style={{ transform: active ? 'scale(1.05)' : 'scale(1)' }}
    />
  )
}

function IconUser({ active }: { active: boolean }) {
  return (
    <svg
      aria-hidden
      className="size-[22px] transition-[stroke,transform] duration-200 ease-out"
      fill="none"
      viewBox="0 0 24 24"
      stroke="currentColor"
      strokeWidth={active ? 2.25 : 1.55}
      style={{ transform: active ? 'scale(1.05)' : 'scale(1)' }}
    >
      <circle cx="12" cy="9" r="3.5" />
      <path d="M6.5 20.2c.7-3.2 3.4-5.2 5.5-5.2s4.8 2 5.5 5.2" strokeLinecap="round" />
    </svg>
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
                  <IconFeed active={isActive} />
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
                  <span className="block [&>svg]:block">
                    <IconSearch active={isActive} />
                  </span>
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
                  <IconUser active={isActive} />
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
