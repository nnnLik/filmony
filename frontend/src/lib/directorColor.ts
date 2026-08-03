const DIRECTOR_PALETTE: readonly string[] = [
  '#5de1d4',
  '#4f87ff',
  '#e8b86d',
  '#ef7d9b',
  '#6366f1',
  '#34d399',
  '#f59e0b',
  '#a78bfa',
  '#fb7185',
  '#38bdf8',
  '#84cc16',
  '#f472b6',
  '#14b8a6',
  '#818cf8',
  '#eab308',
  '#f97316',
]

export type DirectorChipStyles = {
  color: string
  borderClass: string
  backgroundClass: string
}

function hashDirectorId(kinopoiskId: number): number {
  const id = Math.abs(Math.trunc(kinopoiskId))
  return id % DIRECTOR_PALETTE.length
}

export function getDirectorColor(kinopoiskId: number): string {
  return DIRECTOR_PALETTE[hashDirectorId(kinopoiskId)] ?? DIRECTOR_PALETTE[0] ?? '#5de1d4'
}

export function directorChipStyles(kinopoiskId: number): DirectorChipStyles {
  const color = getDirectorColor(kinopoiskId)
  return {
    color,
    borderClass: `border-[color-mix(in_srgb,${color}_45%,var(--tgui--divider_color))]`,
    backgroundClass: `bg-[color-mix(in_srgb,${color}_14%,var(--tgui--secondary_bg_color))]`,
  }
}
