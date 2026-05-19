import type { ReactNode } from 'react'

export function ProfileStatsSectionCard({
  title,
  children,
}: {
  title: string
  children: ReactNode
}) {
  return (
    <section className="rounded-2xl border border-(--tgui--divider_color) bg-(--tgui--secondary_bg_color) p-3 sm:p-4">
      <h3 className="text-sm font-medium leading-snug text-(--tgui--text_color)">{title}</h3>
      <div className="mt-3 w-full min-w-0">{children}</div>
    </section>
  )
}

export function ProfileStatsKpiCard({
  label,
  value,
}: {
  label: string
  value: string | number
}) {
  return (
    <div className="rounded-2xl border border-(--tgui--divider_color) bg-(--tgui--secondary_bg_color) px-4 py-3 sm:p-4">
      <p className="text-xs text-(--tgui--hint_color)">{label}</p>
      <p className="mt-1 text-3xl font-bold tabular-nums tracking-tight text-(--tgui--text_color) sm:text-4xl">{value}</p>
    </div>
  )
}

/** Компактная полоса метрик без крупных одиночных KPI-блоков */
export function ProfileStatsMetricStrip({
  metrics,
}: {
  metrics: readonly { label: string; value: string }[]
}) {
  return (
    <div className="grid grid-cols-2 gap-2">
      {metrics.map((m) => (
        <div
          key={m.label}
          className="min-w-0 rounded-xl border border-[color-mix(in_srgb,var(--tgui--divider_color)_72%,transparent)] bg-(--tgui--bg_color) px-2.5 py-2 sm:px-3 sm:py-2"
        >
          <p className="truncate text-[10px] font-medium leading-tight text-(--tgui--hint_color)">{m.label}</p>
          <p className="mt-0.5 text-base font-semibold tabular-nums tracking-tight text-(--tgui--text_color) sm:text-lg">
            {m.value}
          </p>
        </div>
      ))}
    </div>
  )
}

export type ProfileStatsSummaryRow = {
  label: string
  value: string
  /** Клик по строке (например, применить фильтр и перейти к списку карточек). */
  onActivate?: () => void
}

/** Компактная сводка со строками «метка — значение» для второстепенных блоков */
export function ProfileStatsSummaryCard({
  title,
  rows,
}: {
  title: string
  rows: ProfileStatsSummaryRow[]
}) {
  return (
    <section className="rounded-2xl border border-(--tgui--divider_color) bg-(--tgui--secondary_bg_color) p-3 sm:p-4">
      <h3 className="text-sm font-medium leading-snug text-(--tgui--text_color)">{title}</h3>
      <ul className="mt-3 grid gap-2">
        {rows.map((row) => {
          const inactiveRowClass =
            'flex w-full items-center justify-between gap-3 rounded-xl bg-(--tgui--bg_color) px-3 py-2 text-xs sm:text-sm'
          const sharedLabelClass = 'min-w-0 truncate text-(--tgui--hint_color)'
          const sharedValueClass = 'shrink-0 font-semibold tabular-nums text-(--tgui--text_color)'
          return (
            <li key={row.label}>
              {row.onActivate ? (
                <button
                  type="button"
                  className={`${inactiveRowClass} cursor-pointer text-left outline-none transition-[background-color,opacity] hover:bg-[color-mix(in_srgb,var(--tgui--secondary_bg_color)_35%,var(--tgui--bg_color))] active:opacity-90 focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-(--tgui--link_color)`}
                  onClick={row.onActivate}
                >
                  <span className={sharedLabelClass}>{row.label}</span>
                  <span className={sharedValueClass}>{row.value}</span>
                </button>
              ) : (
                <div className={inactiveRowClass}>
                  <span className={sharedLabelClass}>{row.label}</span>
                  <span className={sharedValueClass}>{row.value}</span>
                </div>
              )}
            </li>
          )
        })}
      </ul>
    </section>
  )
}
