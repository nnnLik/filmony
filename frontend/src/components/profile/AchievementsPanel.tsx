import { Section } from '@telegram-apps/telegram-ui'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useMemo, useState } from 'react'
import { Link } from 'react-router'

import { fetchMyAchievements, updateAchievementPins } from '../../api/achievementsApi'
import type { AchievementItem, MyAchievementsListResponse } from '../../api/achievementsTypes'
import { ApiError, formatApiDetail } from '../../api/client'
import {
  formatAchievementRarity,
  pinnedSlugsFromAchievements,
  sortedAchievements,
} from '../../lib/achievementDisplay'
import { formatQueryError } from '../../lib/formatQueryError'
import { InlineLoadingState } from '../ui/InlineLoadingState'
import { ListErrorState } from '../ui/ListErrorState'

import { AchievementPinPicker } from './AchievementPinPicker'

const achievementsQueryKey = ['me', 'achievements'] as const

function AchievementRow({ item }: { item: AchievementItem }) {
  return (
    <li className="px-4 py-3">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <p className="text-sm font-medium text-(--tgui--text_color)">{item.title}</p>
          {item.description ? (
            <p className="mt-1 text-xs text-(--tgui--hint_color)">{item.description}</p>
          ) : null}
          <Link
            to={`/collections/${encodeURIComponent(item.collection_slug)}`}
            className="mt-1 inline-block text-xs text-(--tgui--link_color) no-underline"
          >
            Открыть коллекцию
          </Link>
        </div>
        <div className="shrink-0 text-right">
          <p className="text-xs font-medium tabular-nums text-(--tgui--link_color)">
            {formatAchievementRarity(item)}
          </p>
          <p className="mt-0.5 text-[10px] uppercase tracking-wide text-(--tgui--hint_color)">
            {item.unlocked ? 'Получено' : 'Заблокировано'}
          </p>
        </div>
      </div>
    </li>
  )
}

type AchievementsPanelProps = {
  className?: string
}

export function AchievementsPanel({ className }: AchievementsPanelProps) {
  const queryClient = useQueryClient()
  const query = useQuery<MyAchievementsListResponse, Error>({
    queryKey: achievementsQueryKey,
    queryFn: fetchMyAchievements,
    staleTime: 60_000,
  })

  const items = useMemo(
    () => sortedAchievements(query.data?.items ?? []),
    [query.data?.items],
  )
  const initialPinned = useMemo(() => pinnedSlugsFromAchievements(items), [items])
  const [draftPins, setDraftPins] = useState<string[] | null>(null)
  const selectedSlugs = draftPins ?? initialPinned
  const [saveError, setSaveError] = useState<string | null>(null)

  const pinMutation = useMutation({
    mutationFn: updateAchievementPins,
    onSuccess: async () => {
      setSaveError(null)
      setDraftPins(null)
      await queryClient.invalidateQueries({ queryKey: achievementsQueryKey })
      await queryClient.invalidateQueries({ queryKey: ['profile'] })
    },
    onError: (error: Error) => {
      setSaveError(
        error instanceof ApiError ? formatApiDetail(error.detail) : error.message,
      )
    },
  })

  const pinsDirty =
    draftPins != null &&
    (draftPins.length !== initialPinned.length ||
      draftPins.some((slug, index) => slug !== initialPinned[index]))

  if (query.isPending) {
    return (
      <div className={className}>
        <InlineLoadingState message="Загрузка достижений…" />
      </div>
    )
  }

  const errorMessage = formatQueryError(query.error, 'Не удалось загрузить достижения')
  if (errorMessage != null) {
    return (
      <div className={className}>
        <ListErrorState
          message={errorMessage}
          onRetry={() => {
            void query.refetch()
          }}
        />
      </div>
    )
  }

  return (
    <div className={className}>
      <AchievementPinPicker
        items={items}
        selectedSlugs={selectedSlugs}
        busy={pinMutation.isPending}
        onChange={(slugs) => {
          setDraftPins(slugs)
          setSaveError(null)
        }}
      />

      {pinsDirty ? (
        <div className="mt-3 flex flex-col gap-2 px-4">
          {saveError != null ? (
            <p className="text-center text-sm text-(--tgui--destructive_text_color)">{saveError}</p>
          ) : null}
          <button
            type="button"
            className="rounded-xl bg-(--tgui--button_color) px-4 py-2.5 text-sm font-medium text-(--tgui--button_text_color) disabled:opacity-60"
            disabled={pinMutation.isPending}
            onClick={() => {
              void pinMutation.mutate(selectedSlugs)
            }}
          >
            {pinMutation.isPending ? 'Сохранение…' : 'Сохранить закрепления'}
          </button>
        </div>
      ) : null}

      <Section header="Все достижения" className="mt-4">
        {items.length === 0 ? (
          <p className="px-4 py-3 text-sm text-(--tgui--hint_color)">
            Каталог достижений пока пуст.
          </p>
        ) : (
          <ul className="divide-y divide-(--tgui--divider_color)">
            {items.map((item) => (
              <AchievementRow key={item.slug} item={item} />
            ))}
          </ul>
        )}
      </Section>
    </div>
  )
}
