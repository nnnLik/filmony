import { Button, Section } from '@telegram-apps/telegram-ui'
import { Pin, PinOff } from 'lucide-react'

import type { AchievementItem } from '../../api/achievementsTypes'
import { formatAchievementRarity } from '../../lib/achievementDisplay'

const MAX_PINS = 3

type AchievementPinPickerProps = {
  items: AchievementItem[]
  selectedSlugs: string[]
  busy?: boolean
  onChange: (slugs: string[]) => void
}

export function AchievementPinPicker({
  items,
  selectedSlugs,
  busy = false,
  onChange,
}: AchievementPinPickerProps) {
  const unlocked = items.filter((item) => item.unlocked)

  const toggleSlug = (slug: string) => {
    if (busy) {
      return
    }
    if (selectedSlugs.includes(slug)) {
      onChange(selectedSlugs.filter((value) => value !== slug))
      return
    }
    if (selectedSlugs.length >= MAX_PINS) {
      return
    }
    onChange([...selectedSlugs, slug])
  }

  return (
    <Section header={`Закрепить на профиле (${selectedSlugs.length}/${MAX_PINS})`}>
      {unlocked.length === 0 ? (
        <p className="px-4 py-3 text-sm text-(--tgui--hint_color)">
          Сначала завершите коллекцию, чтобы закрепить достижение.
        </p>
      ) : (
        <ul className="divide-y divide-(--tgui--divider_color)">
          {unlocked.map((item) => {
            const pinned = selectedSlugs.includes(item.slug)
            const slotIndex = pinned ? selectedSlugs.indexOf(item.slug) + 1 : null
            const disabled = !pinned && selectedSlugs.length >= MAX_PINS
            return (
              <li key={item.slug} className="flex items-center justify-between gap-3 px-4 py-3">
                <div className="min-w-0">
                  <p className="text-sm font-medium text-(--tgui--text_color)">{item.title}</p>
                  <p className="text-xs text-(--tgui--hint_color)">{formatAchievementRarity(item)}</p>
                </div>
                <Button
                  mode={pinned ? 'bezeled' : 'plain'}
                  size="s"
                  disabled={busy || disabled}
                  className="inline-flex shrink-0 items-center gap-1.5"
                  onClick={() => toggleSlug(item.slug)}
                >
                  {pinned ? <PinOff className="block size-4" /> : <Pin className="block size-4" />}
                  {pinned ? `Слот ${slotIndex}` : 'Закрепить'}
                </Button>
              </li>
            )
          })}
        </ul>
      )}
    </Section>
  )
}
