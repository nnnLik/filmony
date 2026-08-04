import type { ReactNode } from 'react'
import { Link } from 'react-router'

import type { MarathonAchievement } from '../../../api/gamificationTypes'

type MarathonShelfFrameProps = {
  marathons: readonly MarathonAchievement[]
  onMarathonDrill?: (marathon: MarathonAchievement) => void
  children: ReactNode
}

function marathonChipLabel(marathon: MarathonAchievement): string {
  const prefix = marathon.kind === 'director' ? 'Режиссёр' : 'Франшиза'
  return `${prefix}: ${marathon.label} · ${marathon.count} фильмов`
}

function marathonChipTo(marathon: MarathonAchievement): string | null {
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

const CHIP_CLASS =
  'rounded-full border border-(--tgui--divider_color) bg-(--tgui--bg_color) px-2.5 py-1 text-[11px] font-medium text-(--tgui--text_color) no-underline outline-none transition active:scale-[0.98] focus-visible:ring-2 focus-visible:ring-(--tgui--link_color)'

export function MarathonShelfFrame({ marathons, onMarathonDrill, children }: MarathonShelfFrameProps) {
  if (marathons.length === 0) {
    return <>{children}</>
  }

  return (
    <div className="rounded-2xl border border-[color-mix(in_srgb,var(--tgui--link_color)_22%,var(--tgui--divider_color))] bg-[color-mix(in_srgb,var(--tgui--secondary_bg_color)_55%,transparent)] p-2 shadow-[inset_0_1px_0_rgba(255,255,255,0.04)]">
      <div className="mb-2 flex flex-wrap gap-1.5 px-0.5">
        {marathons.map((marathon) => {
          const to = marathonChipTo(marathon)
          if (to != null) {
            return (
              <Link key={`${marathon.kind}:${marathon.key}`} to={to} className={CHIP_CLASS}>
                {marathonChipLabel(marathon)}
              </Link>
            )
          }
          return (
            <button
              key={`${marathon.kind}:${marathon.key}`}
              type="button"
              className={CHIP_CLASS}
              onClick={() => onMarathonDrill?.(marathon)}
            >
              {marathonChipLabel(marathon)}
            </button>
          )
        })}
      </div>
      {children}
    </div>
  )
}
