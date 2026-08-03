import { useMemo, useState } from 'react'

import type { MarathonAchievement, PassportStamp } from '../../../api/gamificationTypes'
import { useGamification, usePublicPassport } from '../../../hooks/useGamification'
import {
  getPassportStampMeta,
  PASSPORT_STAMP_CATEGORY_LABELS,
  PASSPORT_STAMP_CATEGORY_ORDER,
  type PassportStampCategory,
} from '../../../lib/gamification/passportStamps'
import { ProfileStatsSectionCard } from '../ProfileStatsSummaryCard'
import { MarathonShelfFrame } from './MarathonShelfFrame'

type ProfilePassportPanelProps = {
  userId: string
  isOwnProfile: boolean
  onMarathonDrill?: (marathon: MarathonAchievement) => void
}

function formatProgress(stamp: PassportStamp): string | null {
  const current = stamp.progress_current
  const target = stamp.progress_target
  if (current == null || target == null || target <= 0) {
    return null
  }
  return `${current}/${target}`
}

function StampTile({
  stamp,
  onSelect,
}: {
  stamp: PassportStamp
  onSelect: (stamp: PassportStamp) => void
}) {
  const meta = getPassportStampMeta(stamp.stamp_id)
  const progress = formatProgress(stamp)

  return (
    <button
      type="button"
      className={`flex min-h-24 flex-col items-center justify-center gap-1 rounded-xl border px-2 py-2 text-center transition active:scale-[0.99] ${
        stamp.unlocked
          ? 'border-[color-mix(in_srgb,var(--tgui--link_color)_35%,var(--tgui--divider_color))] bg-[color-mix(in_srgb,var(--tgui--link_color)_10%,var(--tgui--bg_color))]'
          : 'border-(--tgui--divider_color) bg-(--tgui--secondary_bg_color) opacity-75'
      }`}
      onClick={() => onSelect(stamp)}
    >
      {stamp.unlock_poster_url ? (
        <img
          src={stamp.unlock_poster_url}
          alt=""
          className={`size-10 rounded-md object-cover ${stamp.unlocked ? '' : 'grayscale'}`}
          loading="lazy"
          decoding="async"
        />
      ) : (
        <span
          className={`flex size-10 items-center justify-center rounded-md text-lg ${
            stamp.unlocked ? 'bg-(--tgui--bg_color)' : 'bg-(--tgui--bg_color) text-(--tgui--hint_color)'
          }`}
          aria-hidden
        >
          {stamp.unlocked ? '✓' : '?'}
        </span>
      )}
      <span className="line-clamp-2 text-[10px] font-medium leading-tight text-(--tgui--text_color)">
        {meta.title}
      </span>
      {progress != null ? (
        <span className="text-[9px] tabular-nums text-(--tgui--hint_color)">{progress}</span>
      ) : null}
    </button>
  )
}

function StampDetailModal({
  stamp,
  onClose,
}: {
  stamp: PassportStamp | null
  onClose: () => void
}) {
  if (stamp == null) {
    return null
  }

  const meta = getPassportStampMeta(stamp.stamp_id)
  const progress = formatProgress(stamp)

  return (
    <div
      className="fixed inset-0 z-400 flex items-end justify-center bg-black/45 p-4 sm:items-center"
      role="dialog"
      aria-modal="true"
      aria-labelledby="passport-stamp-title"
      onClick={onClose}
    >
      <div
        className="w-full max-w-sm rounded-2xl border border-(--tgui--divider_color) bg-(--tgui--bg_color) p-4 shadow-xl"
        onClick={(event) => event.stopPropagation()}
      >
        <h3 id="passport-stamp-title" className="text-base font-semibold text-(--tgui--text_color)">
          {meta.title}
        </h3>
        <p className="mt-1 text-sm text-(--tgui--hint_color)">{meta.description}</p>
        {stamp.unlocked && stamp.unlock_film_title ? (
          <p className="mt-3 text-sm text-(--tgui--text_color)">
            Открыл: <span className="font-medium">{stamp.unlock_film_title}</span>
          </p>
        ) : null}
        {!stamp.unlocked && progress != null ? (
          <p className="mt-3 text-sm tabular-nums text-(--tgui--link_color)">Прогресс: {progress}</p>
        ) : null}
        {!stamp.unlocked ? (
          <p className="mt-2 text-xs text-(--tgui--hint_color)">Штамп ещё не получен.</p>
        ) : null}
        <button
          type="button"
          className="mt-4 w-full rounded-xl bg-(--tgui--secondary_bg_color) px-3 py-2.5 text-sm font-medium text-(--tgui--text_color)"
          onClick={onClose}
        >
          Закрыть
        </button>
      </div>
    </div>
  )
}

function groupStampsByCategory(stamps: PassportStamp[]): Map<PassportStampCategory, PassportStamp[]> {
  const grouped = new Map<PassportStampCategory, PassportStamp[]>()
  for (const stamp of stamps) {
    const category = getPassportStampMeta(stamp.stamp_id).category
    const bucket = grouped.get(category) ?? []
    bucket.push(stamp)
    grouped.set(category, bucket)
  }
  return grouped
}

export function ProfilePassportPanel({ userId, isOwnProfile, onMarathonDrill }: ProfilePassportPanelProps) {
  const ownQuery = useGamification({ enabled: isOwnProfile })
  const publicQuery = usePublicPassport(userId, { enabled: !isOwnProfile })
  const [selectedStamp, setSelectedStamp] = useState<PassportStamp | null>(null)

  const loading = isOwnProfile ? ownQuery.isLoading : publicQuery.isLoading
  const error = isOwnProfile ? ownQuery.error : publicQuery.error

  const stamps = useMemo(() => {
    if (isOwnProfile) {
      return ownQuery.data?.passport.stamps ?? []
    }
    return publicQuery.data?.stamps ?? []
  }, [isOwnProfile, ownQuery.data, publicQuery.data])

  const unlockedCount = useMemo(() => {
    if (isOwnProfile) {
      return ownQuery.data?.passport.unlocked_count ?? stamps.filter((stamp) => stamp.unlocked).length
    }
    return publicQuery.data?.unlocked_count ?? stamps.filter((stamp) => stamp.unlocked).length
  }, [isOwnProfile, ownQuery.data, publicQuery.data, stamps])

  const marathons = isOwnProfile ? (ownQuery.data?.marathons ?? []) : []

  const visibleStamps = useMemo(
    () => (isOwnProfile ? stamps : stamps.filter((stamp) => stamp.unlocked)),
    [isOwnProfile, stamps],
  )

  const stampsByCategory = useMemo(() => groupStampsByCategory(visibleStamps), [visibleStamps])

  if (loading) {
    return <p className="text-sm text-(--tgui--hint_color)">Загрузка коллекции…</p>
  }

  if (error != null) {
    return (
      <p className="text-sm text-(--tgui--hint_color)">
        {isOwnProfile ? 'Коллекция скоро появится — данные временно недоступны.' : 'Коллекция недоступна.'}
      </p>
    )
  }

  return (
    <>
      <ProfileStatsSectionCard title="Кино-паспорт">
        <p className="mb-3 text-xs text-(--tgui--hint_color)">
          {isOwnProfile
            ? `Открыто штампов: ${unlockedCount}`
            : unlockedCount > 0
              ? `Публичных штампов: ${unlockedCount}`
              : 'Пока нет открытых штампов'}
        </p>
        {visibleStamps.length === 0 ? (
          <p className="text-sm text-(--tgui--hint_color)">Пока нет штампов для показа.</p>
        ) : (
          <div className="space-y-4">
            {PASSPORT_STAMP_CATEGORY_ORDER.map((category) => {
              const sectionStamps = stampsByCategory.get(category)
              if (sectionStamps == null || sectionStamps.length === 0) {
                return null
              }
              return (
                <section key={category}>
                  <h4 className="mb-2 text-xs font-semibold uppercase tracking-wide text-(--tgui--hint_color)">
                    {PASSPORT_STAMP_CATEGORY_LABELS[category]}
                  </h4>
                  <div className="grid grid-cols-3 gap-2 sm:grid-cols-4">
                    {sectionStamps.map((stamp) => (
                      <StampTile key={stamp.stamp_id} stamp={stamp} onSelect={setSelectedStamp} />
                    ))}
                  </div>
                </section>
              )
            })}
          </div>
        )}
      </ProfileStatsSectionCard>

      {isOwnProfile && marathons.length > 0 ? (
        <ProfileStatsSectionCard title="Марафоны">
          <MarathonShelfFrame marathons={marathons} onMarathonDrill={onMarathonDrill}>
            <p className="px-1 py-2 text-xs text-(--tgui--hint_color)">
              Нажмите на марафон, чтобы отфильтровать оценённые карточки.
            </p>
          </MarathonShelfFrame>
        </ProfileStatsSectionCard>
      ) : null}

      <StampDetailModal stamp={selectedStamp} onClose={() => setSelectedStamp(null)} />
    </>
  )
}
