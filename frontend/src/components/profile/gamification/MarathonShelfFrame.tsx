import type { ReactNode } from 'react'

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

export function MarathonShelfFrame({ marathons, onMarathonDrill, children }: MarathonShelfFrameProps) {
  if (marathons.length === 0) {
    return <>{children}</>
  }

  return (
    <div className="rounded-2xl border border-[color-mix(in_srgb,var(--tgui--link_color)_22%,var(--tgui--divider_color))] bg-[color-mix(in_srgb,var(--tgui--secondary_bg_color)_55%,transparent)] p-2 shadow-[inset_0_1px_0_rgba(255,255,255,0.04)]">
      <div className="mb-2 flex flex-wrap gap-1.5 px-0.5">
        {marathons.map((marathon) => (
          <button
            key={`${marathon.kind}:${marathon.key}`}
            type="button"
            className="rounded-full border border-(--tgui--divider_color) bg-(--tgui--bg_color) px-2.5 py-1 text-[11px] font-medium text-(--tgui--text_color) transition active:scale-[0.98]"
            onClick={() => onMarathonDrill?.(marathon)}
          >
            {marathonChipLabel(marathon)}
          </button>
        ))}
      </div>
      {children}
    </div>
  )
}
