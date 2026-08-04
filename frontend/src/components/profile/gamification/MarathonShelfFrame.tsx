import type { ReactNode } from 'react'
import { Link } from 'react-router'

import type { MarathonAchievement } from '../../../api/gamificationTypes'

type MarathonShelfFrameProps = {
  marathons: readonly MarathonAchievement[]
  onMarathonDrill?: (marathon: MarathonAchievement) => void
  children: ReactNode
}

function marathonKindLabel(marathon: MarathonAchievement): string {
  return marathon.kind === 'director' ? 'Режиссёр' : 'Франшиза'
}

function marathonFilmCountLabel(count: number): string {
  return `${count} ${count === 1 ? 'фильм' : count < 5 ? 'фильма' : 'фильмов'}`
}

function marathonLinkTo(marathon: MarathonAchievement): string | null {
  if (marathon.kind === 'director') {
    const parsed = Number.parseInt(marathon.key, 10)
    if (Number.isInteger(parsed) && parsed >= 1) {
      return `/directors/${parsed}`
    }
    return null
  }
  if (marathon.kind === 'franchise') {
    const key = marathon.key.trim()
    if (key !== '') {
      return `/franchises/${encodeURIComponent(key)}`
    }
  }
  return null
}

export function MarathonShelfFrame({ marathons, onMarathonDrill, children }: MarathonShelfFrameProps) {
  if (marathons.length === 0) {
    return <>{children}</>
  }

  return (
    <div className="rounded-2xl border border-[color-mix(in_srgb,var(--tgui--link_color)_22%,var(--tgui--divider_color))] bg-[color-mix(in_srgb,var(--tgui--secondary_bg_color)_55%,transparent)] p-2 shadow-[inset_0_1px_0_rgba(255,255,255,0.04)]">
      <ul className="mb-2 divide-y divide-(--tgui--divider_color) overflow-hidden rounded-xl border border-(--tgui--divider_color)">
        {marathons.map((marathon) => {
          const to = marathonLinkTo(marathon)
          const title = (
            <>
              {marathon.label}
              {' · '}
              {marathonFilmCountLabel(marathon.count)}
            </>
          )

          return (
            <li key={`${marathon.kind}:${marathon.key}`} className="px-3 py-2.5">
              <p className="text-[11px] text-(--tgui--hint_color)">{marathonKindLabel(marathon)}</p>
              <p className="text-sm font-medium">
                {to != null ? (
                  <Link to={to} className="text-(--tgui--link_color) no-underline">
                    {title}
                  </Link>
                ) : (
                  <button
                    type="button"
                    className="text-left text-(--tgui--text_color)"
                    onClick={() => onMarathonDrill?.(marathon)}
                  >
                    {title}
                  </button>
                )}
              </p>
            </li>
          )
        })}
      </ul>
      {children}
    </div>
  )
}
