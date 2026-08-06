import { Section } from '@telegram-apps/telegram-ui'
import { Link } from 'react-router'

import type { PinnedAchievement } from '../../api/achievementsTypes'
import { formatAchievementRarity } from '../../lib/achievementDisplay'

type PublicProfilePinnedAchievementsProps = {
  items: PinnedAchievement[]
  className?: string
}

export function PublicProfilePinnedAchievements({
  items,
  className,
}: PublicProfilePinnedAchievementsProps) {
  if (items.length === 0) {
    return null
  }

  const sorted = [...items].sort((a, b) => a.slot_index - b.slot_index)

  return (
    <div className={className}>
      <Section header="Достижения">
        <ul className="divide-y divide-(--tgui--divider_color)">
          {sorted.map((item) => (
            <li key={item.slug} className="px-4 py-3">
              <div className="flex items-start justify-between gap-3">
                <div className="min-w-0">
                  <p className="text-sm font-medium text-(--tgui--text_color)">{item.title}</p>
                  <Link
                    to={`/collections/${encodeURIComponent(item.collection_slug)}`}
                    className="mt-1 inline-block text-xs text-(--tgui--link_color) no-underline"
                  >
                    Коллекция
                  </Link>
                </div>
                <p className="shrink-0 text-xs font-medium tabular-nums text-(--tgui--link_color)">
                  {formatAchievementRarity(item)}
                </p>
              </div>
            </li>
          ))}
        </ul>
      </Section>
    </div>
  )
}
