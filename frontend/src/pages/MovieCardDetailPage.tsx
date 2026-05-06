import { Button, Title } from '@telegram-apps/telegram-ui'
import { useEffect, useMemo, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'

import { ApiError, formatApiDetail } from '../api/client'
import { getMovieCardById } from '../api/cardApi'
import type { CardCompany, CardMoodAfter, CardMoodBefore, MovieCard } from '../api/profileTypes'

const COMPANY_LABELS: Record<CardCompany, string> = {
  alone: 'Один',
  partner: 'С партнером',
  friends: 'С друзьями',
  family: 'С семьей',
}

const MOOD_BEFORE_LABELS: Record<CardMoodBefore, string> = {
  relax: 'Расслабиться',
  laugh: 'Поржать',
  sad: 'Погрустить',
  thrill: 'Напряжение',
}

const MOOD_AFTER_LABELS: Record<CardMoodAfter, string> = {
  laughed: 'Веселый',
  cried: 'Плакал',
  enjoyed: 'Кайфанул',
  tense: 'Уставший',
  wasted_time: 'Зря потратил время',
}

function formatRating(value: number): string {
  return Number.isInteger(value) ? String(value) : value.toFixed(1)
}

function scoreColor(score: number): string {
  if (score <= 3) return 'bg-[#ef4444]'
  if (score <= 5) return 'bg-[#f59e0b]'
  if (score <= 7) return 'bg-[#84cc16]'
  return 'bg-[#22c55e]'
}

function ratingScale(current: number): number[] {
  return Array.from({ length: 10 }, (_v, index) => index + 1).map((score) =>
    score === 10 ? 10 : score
  )
}

export function MovieCardDetailPage() {
  const navigate = useNavigate()
  const { cardId } = useParams<{ cardId?: string }>()
  const [card, setCard] = useState<MovieCard | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const parsedCardId = useMemo(() => {
    if (cardId == null) return null
    const value = Number(cardId)
    return Number.isInteger(value) && value > 0 ? value : null
  }, [cardId])

  useEffect(() => {
    if (parsedCardId == null) {
      setError('Некорректный id карточки')
      setLoading(false)
      return
    }
    let alive = true
    void (async () => {
      setLoading(true)
      setError(null)
      try {
        const item = await getMovieCardById(parsedCardId)
        if (!alive) return
        setCard(item)
      } catch (e) {
        if (!alive) return
        if (e instanceof ApiError) {
          setError(formatApiDetail(e.detail))
        } else {
          setError('Не удалось загрузить карточку фильма')
        }
      } finally {
        if (alive) {
          setLoading(false)
        }
      }
    })()
    return () => {
      alive = false
    }
  }, [parsedCardId])

  return (
    <div className="min-h-dvh bg-(--tgui--bg_color) text-(--tgui--text_color)">
      <header className="sticky top-0 z-20 border-b border-(--tgui--divider_color) bg-[color-mix(in_srgb,var(--tgui--bg_color)_88%,transparent)] backdrop-blur-md">
        <div className="flex items-center gap-2 px-3 py-2">
          <button
            type="button"
            onClick={() => navigate(-1)}
            className="flex min-h-10 min-w-10 items-center justify-center rounded-lg text-lg text-(--tgui--link_color)"
            aria-label="Назад"
          >
            ←
          </button>
          <span className="truncate text-sm font-medium text-(--tgui--hint_color)">
            {card?.film_title ?? 'Карточка фильма'}
          </span>
        </div>
      </header>

      <main className="mx-auto max-w-md px-4 py-4">
        {loading ? <p className="filmony-text-panel py-10 text-center text-sm text-(--tgui--hint_color)">Загрузка…</p> : null}

        {error != null ? (
          <div className="py-10 text-center">
            <p className="filmony-text-panel text-sm text-(--tgui--destructive_text_color)">{error}</p>
            <Link to="/profile" className="mt-3 inline-block text-sm text-(--tgui--link_color)">
              Вернуться в профиль
            </Link>
          </div>
        ) : null}

        {!loading && error == null && card != null ? (
          <div className="space-y-4">
            <div className="overflow-hidden rounded-2xl border border-(--tgui--divider_color) bg-(--tgui--secondary_bg_color)">
              <div className="aspect-video w-full">
                {card.film_poster_url ? (
                  <img src={card.film_poster_url} alt={card.film_title} className="h-full w-full object-cover" />
                ) : (
                  <div className="flex h-full items-center justify-center text-sm text-(--tgui--hint_color)">Нет постера</div>
                )}
              </div>
              <div className="px-4 py-3">
                <Title level="2" weight="2">
                  {card.film_title}
                </Title>
                <p className="mt-1 text-sm text-(--tgui--hint_color)">{card.film_year ?? 'Год неизвестен'}</p>
              </div>
            </div>

            <section className="rounded-2xl border border-(--tgui--divider_color) bg-(--tgui--secondary_bg_color) p-4">
              <p className="text-sm font-medium text-(--tgui--text_color)">Твоя оценка</p>
              <div className="mt-3 flex flex-wrap gap-2">
                {ratingScale(card.rating).map((score) => (
                  <div
                    key={score}
                    className={`flex h-8 w-8 items-center justify-center rounded-full text-xs font-semibold text-white ${
                      scoreColor(score)
                    } ${Math.round(card.rating) === score ? 'ring-2 ring-white/80' : 'opacity-80'}`}
                  >
                    {score}
                  </div>
                ))}
              </div>
              <p className="mt-2 text-xs text-(--tgui--hint_color)">Итог: {formatRating(card.rating)}</p>
            </section>

            <section className="rounded-2xl border border-(--tgui--divider_color) bg-(--tgui--secondary_bg_color) p-4">
              <p className="text-sm font-medium text-(--tgui--text_color)">Теги</p>
              <div className="mt-3 flex flex-wrap gap-2">
                <span className="rounded-full bg-[#1e3a5f] px-3 py-1.5 text-xs text-white">{COMPANY_LABELS[card.company]}</span>
                <span className="rounded-full bg-[#0f172a] px-3 py-1.5 text-xs text-white">
                  {MOOD_BEFORE_LABELS[card.mood_before]}
                </span>
                <span className="rounded-full bg-[#1d4ed8] px-3 py-1.5 text-xs text-white">
                  {MOOD_AFTER_LABELS[card.mood_after]}
                </span>
              </div>
              <p className="mt-4 text-sm font-medium text-(--tgui--text_color)">Свои теги</p>
              <div className="mt-2 flex flex-wrap gap-2">
                {card.custom_tags.length > 0 ? (
                  card.custom_tags.map((tag) => (
                    <span
                      key={tag}
                      className="rounded-lg border border-(--tgui--divider_color) bg-(--tgui--bg_color) px-2 py-1 text-xs"
                    >
                      {tag}
                    </span>
                  ))
                ) : (
                  <span className="text-xs text-(--tgui--hint_color)">Пока нет собственных тегов</span>
                )}
              </div>
            </section>

            <section className="rounded-2xl border border-(--tgui--divider_color) bg-(--tgui--secondary_bg_color) p-4">
              <div className="flex gap-2">
                <Button stretched mode="gray" disabled>
                  Пригласить друзей (mock)
                </Button>
                <Button stretched mode="gray" disabled>
                  Рекомендовать (mock)
                </Button>
              </div>
            </section>

            <section className="rounded-2xl border border-(--tgui--divider_color) bg-(--tgui--secondary_bg_color) p-4">
              <p className="text-sm font-medium">Друзья оценили</p>
              <div className="mt-3 space-y-2 text-sm text-(--tgui--hint_color)">
                <p>Аня — 10</p>
                <p>Максим — 8</p>
                <p>Катя — 9</p>
              </div>
            </section>

            <section className="rounded-2xl border border-(--tgui--divider_color) bg-(--tgui--secondary_bg_color) p-4">
              <p className="text-sm font-medium">Лучшая оценка</p>
              <p className="mt-2 text-sm text-(--tgui--hint_color)">Аня — 10</p>
            </section>

            <section className="rounded-2xl border border-(--tgui--divider_color) bg-(--tgui--secondary_bg_color) p-4">
              <p className="text-sm font-medium">Комментарии</p>
              <div className="mt-3 space-y-3 text-sm">
                <p>
                  <span className="font-medium">Аня:</span> Киллиан — гений! Лучшая роль года.
                </p>
                <p>
                  <span className="font-medium">Максим:</span> Затянуто местами, но финал оправдывает всё.
                </p>
              </div>
              <p className="mt-3 text-xs text-(--tgui--hint_color)">Этот блок пока статический mock.</p>
            </section>
          </div>
        ) : null}
      </main>
    </div>
  )
}
