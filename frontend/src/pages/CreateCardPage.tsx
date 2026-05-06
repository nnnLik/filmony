import { Button, Cell, Input, List, Section, Title } from '@telegram-apps/telegram-ui'
import { useEffect, useState } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'

import { ApiError, formatApiDetail } from '../api/client'
import { createMovieCard, getFilmById, resolveFilmByKinopoiskUrl } from '../api/cardApi'
import type { CardCompany, CardMoodAfter, CardMoodBefore, Film } from '../api/profileTypes'
import { clearMyProfileBundleCache } from '../lib/myProfileBundleCache'

const COMPANY_OPTIONS: Array<{ value: CardCompany; label: string }> = [
  { value: 'alone', label: 'Один' },
  { value: 'partner', label: 'С партнером' },
  { value: 'friends', label: 'С друзьями' },
  { value: 'family', label: 'С семьей' },
]

const MOOD_BEFORE_OPTIONS: Array<{ value: CardMoodBefore; label: string }> = [
  { value: 'relax', label: 'Хотел расслабиться' },
  { value: 'laugh', label: 'Хотел поржать' },
  { value: 'sad', label: 'Хотел погрустить' },
  { value: 'thrill', label: 'Хотел напряжения' },
]

const MOOD_AFTER_OPTIONS: Array<{ value: CardMoodAfter; label: string }> = [
  { value: 'laughed', label: 'Угарал' },
  { value: 'cried', label: 'Плакал' },
  { value: 'enjoyed', label: 'Кайфанул' },
  { value: 'tense', label: 'Был напряжен' },
  { value: 'wasted_time', label: 'Зря потратил время' },
]

function normalizeRating(value: number): number {
  const clamped = Math.max(1, Math.min(10, value))
  return Math.round(clamped * 2) / 2
}

function formatRating(value: number): string {
  return Number.isInteger(value) ? String(value) : value.toFixed(1)
}

export function CreateCardPage() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const initialFilmId = searchParams.get('filmId')
  const [kinopoiskUrl, setKinopoiskUrl] = useState('')
  const [loadingFilm, setLoadingFilm] = useState(false)
  const [submitLoading, setSubmitLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [film, setFilm] = useState<Film | null>(null)
  const [rating, setRating] = useState(7.5)
  const [company, setCompany] = useState<CardCompany>('alone')
  const [moodBefore, setMoodBefore] = useState<CardMoodBefore>('relax')
  const [moodAfter, setMoodAfter] = useState<CardMoodAfter>('enjoyed')
  const [customTags, setCustomTags] = useState<string[]>([])
  const [tagInput, setTagInput] = useState('')

  useEffect(() => {
    if (initialFilmId == null || initialFilmId === '') {
      return
    }
    const filmId = Number(initialFilmId)
    if (!Number.isInteger(filmId) || filmId <= 0) {
      return
    }
    void (async () => {
      setLoadingFilm(true)
      try {
        const item = await getFilmById(filmId)
        setFilm(item)
      } catch (e) {
        if (e instanceof ApiError) {
          setError(formatApiDetail(e.detail))
        } else {
          setError('Не удалось загрузить фильм')
        }
      } finally {
        setLoadingFilm(false)
      }
    })()
  }, [initialFilmId])

  async function handleResolveFilm() {
    if (kinopoiskUrl.trim() === '') {
      setError('Вставьте ссылку на Кинопоиск')
      return
    }
    setLoadingFilm(true)
    setError(null)
    try {
      const item = await resolveFilmByKinopoiskUrl(kinopoiskUrl.trim())
      setFilm(item)
    } catch (e) {
      if (e instanceof ApiError) {
        setError(formatApiDetail(e.detail))
      } else {
        setError('Не удалось получить фильм по ссылке')
      }
    } finally {
      setLoadingFilm(false)
    }
  }

  function addTag() {
    const trimmed = tagInput.trim()
    if (trimmed === '') {
      return
    }
    const lowered = trimmed.toLowerCase()
    if (customTags.some((tag) => tag.toLowerCase() === lowered)) {
      setTagInput('')
      return
    }
    if (customTags.length >= 5) {
      setError('Можно добавить не больше 5 тегов')
      return
    }
    setCustomTags((prev) => [...prev, trimmed])
    setTagInput('')
    setError(null)
  }

  function removeTag(tag: string) {
    setCustomTags((prev) => prev.filter((item) => item !== tag))
  }

  async function handleSubmit() {
    if (film == null) {
      setError('Сначала выберите фильм')
      return
    }
    setSubmitLoading(true)
    setError(null)
    try {
      await createMovieCard({
        film_id: film.id,
        rating: normalizeRating(rating),
        company,
        mood_before: moodBefore,
        mood_after: moodAfter,
        custom_tags: customTags,
      })
      clearMyProfileBundleCache()
      void navigate('/profile')
    } catch (e) {
      if (e instanceof ApiError) {
        setError(formatApiDetail(e.detail))
      } else {
        setError('Не удалось создать карточку')
      }
    } finally {
      setSubmitLoading(false)
    }
  }

  return (
    <div className="min-h-full">
      <header className="sticky top-0 z-20 border-b border-(--tgui--divider_color) bg-[color-mix(in_srgb,var(--tgui--bg_color)_88%,transparent)] backdrop-blur-md">
        <div className="flex items-center justify-between px-4 py-3">
          <Link
            to="/"
            className="flex h-10 w-10 items-center justify-center rounded-xl text-lg text-(--tgui--link_color) no-underline active:opacity-70"
            aria-label="Назад"
          >
            ←
          </Link>
          <h1 className="text-lg font-semibold tracking-tight text-(--tgui--text_color)">Добавить фильм</h1>
          <span className="w-10" />
        </div>
      </header>

      <main className="px-4 py-6">
        <Section header="Ссылка на Кинопоиск">
          <div className="flex flex-col gap-3 px-3 py-3">
            <Input
              header="URL"
              type="url"
              placeholder="https://www.kinopoisk.ru/film/..."
              value={kinopoiskUrl}
              onChange={(e) => setKinopoiskUrl(e.currentTarget.value)}
            />
            <Button stretched loading={loadingFilm} onClick={() => void handleResolveFilm()}>
              Получить фильм
            </Button>
          </div>
        </Section>

        {film != null ? (
          <Section header="Предпросмотр">
            <div className="filmony-text-panel mx-3 my-3 flex gap-3">
              <div className="h-24 w-16 shrink-0 overflow-hidden rounded-lg bg-(--tgui--secondary_bg_color)">
                {film.poster_url ? (
                  <img src={film.poster_url} alt={film.title} className="h-full w-full object-cover" />
                ) : null}
              </div>
              <div className="min-w-0">
                <Title level="3" weight="2">
                  {film.title}
                </Title>
                <p className="mt-1 text-sm text-(--tgui--hint_color)">{film.year ?? 'Год неизвестен'}</p>
                <p className="mt-2 text-xs text-(--tgui--hint_color)">film_id: {film.id}</p>
              </div>
            </div>
          </Section>
        ) : (
          <p className="filmony-text-panel mt-4 text-center text-sm text-(--tgui--hint_color)">
            После резолва ссылки здесь появится предпросмотр фильма.
          </p>
        )}

        <Section header="Оценка">
          <div className="px-3 py-3">
            <div className="filmony-text-panel">
              <p className="text-sm text-(--tgui--hint_color)">Текущая оценка</p>
              <p className="mt-1 text-2xl font-bold text-(--tgui--text_color)">{formatRating(rating)}</p>
              <div className="mt-3 flex gap-2">
                <Button mode="gray" size="s" onClick={() => setRating((v) => normalizeRating(v - 0.5))}>
                  -0.5
                </Button>
                <Button mode="gray" size="s" onClick={() => setRating((v) => normalizeRating(v + 0.5))}>
                  +0.5
                </Button>
              </div>
            </div>
          </div>
        </Section>

        <Section header="Теги контекста">
          <List>
            {COMPANY_OPTIONS.map((option) => (
              <Cell
                key={option.value}
                multiline
                subtitle="С кем смотрели"
                before={company === option.value ? '✓' : undefined}
                onClick={() => setCompany(option.value)}
              >
                {option.label}
              </Cell>
            ))}
            {MOOD_BEFORE_OPTIONS.map((option) => (
              <Cell
                key={option.value}
                multiline
                subtitle="Настроение до"
                before={moodBefore === option.value ? '✓' : undefined}
                onClick={() => setMoodBefore(option.value)}
              >
                {option.label}
              </Cell>
            ))}
            {MOOD_AFTER_OPTIONS.map((option) => (
              <Cell
                key={option.value}
                multiline
                subtitle="Настроение после"
                before={moodAfter === option.value ? '✓' : undefined}
                onClick={() => setMoodAfter(option.value)}
              >
                {option.label}
              </Cell>
            ))}
          </List>
        </Section>

        <Section header="Свои теги (до 5)">
          <div className="px-3 py-3">
            <div className="flex gap-2">
              <Input
                placeholder="Добавить тег"
                value={tagInput}
                onChange={(e) => setTagInput(e.currentTarget.value)}
              />
              <Button mode="gray" onClick={addTag}>
                Добавить
              </Button>
            </div>
            {customTags.length > 0 ? (
              <div className="mt-3 flex flex-wrap gap-2">
                {customTags.map((tag) => (
                  <button
                    key={tag}
                    type="button"
                    className="rounded-full border border-(--tgui--divider_color) bg-(--tgui--secondary_bg_color) px-3 py-1 text-xs text-(--tgui--text_color)"
                    onClick={() => removeTag(tag)}
                    title="Удалить тег"
                  >
                    {tag} ×
                  </button>
                ))}
              </div>
            ) : null}
          </div>
        </Section>

        {error != null ? (
          <p className="filmony-text-panel mt-4 text-sm text-(--tgui--destructive_text_color)">{error}</p>
        ) : null}

        <div className="mt-6">
          <Button stretched loading={submitLoading} disabled={film == null} onClick={() => void handleSubmit()}>
            Создать карточку
          </Button>
        </div>
      </main>
    </div>
  )
}
