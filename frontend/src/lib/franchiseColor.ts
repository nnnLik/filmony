const FRANCHISE_PALETTE: readonly string[] = [
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

export type FranchiseChipStyles = {
  color: string
  borderClass: string
  backgroundClass: string
}

function hashFranchiseKey(franchiseKey: string): number {
  const key = franchiseKey.trim()
  let hash = 0
  for (let i = 0; i < key.length; i += 1) {
    hash = (hash * 31 + key.charCodeAt(i)) >>> 0
  }
  return hash % FRANCHISE_PALETTE.length
}

export function getFranchiseColor(franchiseKey: string): string {
  const trimmed = franchiseKey.trim()
  if (trimmed === '') {
    return FRANCHISE_PALETTE[0] ?? '#5de1d4'
  }
  return FRANCHISE_PALETTE[hashFranchiseKey(trimmed)] ?? FRANCHISE_PALETTE[0] ?? '#5de1d4'
}

export function franchiseChipStyles(franchiseKey: string): FranchiseChipStyles {
  const color = getFranchiseColor(franchiseKey)
  return {
    color,
    borderClass: `border-[color-mix(in_srgb,${color}_45%,var(--tgui--divider_color))]`,
    backgroundClass: `bg-[color-mix(in_srgb,${color}_14%,var(--tgui--secondary_bg_color))]`,
  }
}
