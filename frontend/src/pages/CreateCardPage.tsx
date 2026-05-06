import { Button, Input, Section, Title } from '@telegram-apps/telegram-ui'
import { useEffect, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'

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

const CHIP_COLORS = [
  'bg-[#3B82F633] text-[#60A5FA]',
  'bg-[#F9731633] text-[#FDBA74]',
  'bg-[#22C55E33] text-[#86EFAC]',
  'bg-[#A855F733] text-[#D8B4FE]',
  'bg-[#EC489933] text-[#F9A8D4]',
] as const

type WizardStep = 1 | 2 | 3 | 4 | 5
const TOTAL_STEPS = 5
const STEP_TITLES: Record<WizardStep, string> = {
  1: 'Ссылка на фильм',
  2: 'Подтверждение',
  3: 'Оценка и контекст',
  4: 'Ваши теги',
  5: 'Финальный шаг',
}

function normalizeRating(value: number): number {
  const clamped = Math.max(1, Math.min(10, value))
  return Math.round(clamped * 2) / 2
}

function formatRating(value: number): string {
  return Number.isInteger(value) ? String(value) : value.toFixed(1)
}

function mapResolveError(detail: string): string {
  const normalized = detail.toLowerCase()
  if (normalized.includes('empty url')) {
    return 'Вставьте ссылку на фильм Кинопоиска.'
  }
  if (normalized.includes('url must be from kinopoisk.ru')) {
    return 'Ссылка должна быть с сайта kinopoisk.ru.'
  }
  if (normalized.includes('film id was not found in url')) {
    return 'Не удалось распознать id фильма в ссылке. Пример: https://www.kinopoisk.ru/film/6764/'
  }
  return detail
}

export function CreateCardPage() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const initialFilmId = searchParams.get('filmId')
  const [step, setStep] = useState<WizardStep>(1)
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
        setStep(2)
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
      setStep(2)
    } catch (e) {
      if (e instanceof ApiError) {
        setError(mapResolveError(formatApiDetail(e.detail)))
      } else {
        setError('Не удалось получить информацию о фильме. Проверьте ссылку и попробуйте снова.')
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

  function goBack() {
    if (step === 1) {
      void navigate('/')
      return
    }
    setError(null)
    setStep((prev) => (prev - 1) as WizardStep)
  }

  function renderChoiceChips<T extends string>(
    options: Array<{ value: T; label: string }>,
    selected: T,
    onSelect: (value: T) => void
  ) {
    return (
      <div className="mt-2 flex flex-wrap gap-2">
        {options.map((option, index) => {
          const isSelected = option.value === selected
          const color = CHIP_COLORS[index % CHIP_COLORS.length]
          return (
            <button
              key={option.value}
              type="button"
              onClick={() => onSelect(option.value)}
              className={`rounded-xl border px-3 py-2 text-xs font-medium transition active:scale-[0.99] ${
                isSelected
                  ? 'border-(--tgui--link_color) ring-1 ring-(--tgui--link_color) shadow-[0_0_0_1px_color-mix(in_srgb,var(--tgui--link_color)_20%,transparent)]'
                  : 'border-(--tgui--divider_color) opacity-90'
              } ${color}`}
            >
              {option.label}
            </button>
          )
        })}
      </div>
    )
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
        kinopoisk_id: film.kinopoisk_id,
        genres: film.genres ?? [],
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
        <div className="flex items-center justify-between px-4 pb-2 pt-3">
          <button
            type="button"
            onClick={goBack}
            className="flex h-10 w-10 items-center justify-center rounded-xl text-lg text-(--tgui--link_color) active:opacity-70"
            aria-label="Назад"
          >
            ←
          </button>
          <div className="text-center">
            <h1 className="text-base font-semibold tracking-tight text-(--tgui--text_color)">Новая карточка</h1>
            <p className="text-xs text-(--tgui--hint_color)">
              Шаг {step} из {TOTAL_STEPS}: {STEP_TITLES[step]}
            </p>
          </div>
          <span className="w-10" />
        </div>
        <div className="px-4 pb-3">
          <div className="h-1.5 overflow-hidden rounded-full bg-(--tgui--secondary_bg_color)">
            <div
              className="h-full rounded-full bg-(--tgui--link_color) transition-all duration-300"
              style={{ width: `${(step / TOTAL_STEPS) * 100}%` }}
            />
          </div>
        </div>
      </header>

      <main className="px-4 py-6">
        {step === 1 ? (
          <Section header="1. Ссылка на Кинопоиск">
            <div className="flex flex-col gap-4 px-3 py-3">
              <p className="text-sm text-(--tgui--hint_color)">
                Вставьте ссылку вида <span className="text-(--tgui--text_color)">kinopoisk.ru/film/6764/</span>
              </p>
              <Input
                header="URL"
                placeholder="https://www.kinopoisk.ru/film/6764/"
                value={kinopoiskUrl}
                onChange={(e) => setKinopoiskUrl(e.currentTarget.value)}
              />
              <Button stretched disabled={loadingFilm} onClick={() => void handleResolveFilm()}>
                {loadingFilm ? 'Загружаем...' : 'Далее'}
              </Button>
            </div>
          </Section>
        ) : null}

        {step === 2 ? (
          <Section header="2. Подтверждение фильма">
            {film != null ? (
              <div className="px-3 py-3">
                <div className="filmony-text-panel flex gap-3">
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
                  </div>
                </div>
                <p className="mt-4 text-sm text-(--tgui--hint_color)">Это тот фильм?</p>
                <div className="mt-3 flex flex-col gap-2 sm:flex-row">
                  <Button
                    mode="gray"
                    stretched
                    onClick={() => {
                      setFilm(null)
                      setError(null)
                      setStep(1)
                    }}
                  >
                    Нет, другой фильм
                  </Button>
                  <Button stretched onClick={() => setStep(3)}>
                    Да, далее
                  </Button>
                </div>
              </div>
            ) : (
              <div className="px-3 py-3">
                <p className="filmony-text-panel text-sm text-(--tgui--hint_color)">
                  Фильм не найден. Вернитесь к шагу 1 и введите ссылку снова.
                </p>
                <div className="mt-3">
                  <Button stretched onClick={() => setStep(1)}>
                    К ссылке
                  </Button>
                </div>
              </div>
            )}
          </Section>
        ) : null}

        {step === 3 ? (
          <Section header="3. Оценка и теги">
            <div className="px-3 py-3">
              <div className="filmony-text-panel text-center">
                <p className="text-sm text-(--tgui--hint_color)">Оценка</p>
                <p className="mt-1 text-4xl font-bold text-(--tgui--text_color)">{formatRating(rating)}</p>
                <div className="mt-3 flex justify-center gap-2">
                  <Button mode="gray" size="s" onClick={() => setRating((v) => normalizeRating(v - 0.5))}>
                    -0.5
                  </Button>
                  <Button mode="gray" size="s" onClick={() => setRating((v) => normalizeRating(v + 0.5))}>
                    +0.5
                  </Button>
                </div>
              </div>

              <div className="mt-4">
                <p className="text-sm font-medium text-(--tgui--text_color)">С кем смотрели:</p>
                {renderChoiceChips(COMPANY_OPTIONS, company, setCompany)}
              </div>

              <div className="mt-4">
                <p className="text-sm font-medium text-(--tgui--text_color)">До просмотра:</p>
                {renderChoiceChips(MOOD_BEFORE_OPTIONS, moodBefore, setMoodBefore)}
              </div>

              <div className="mt-4">
                <p className="text-sm font-medium text-(--tgui--text_color)">После просмотра:</p>
                {renderChoiceChips(MOOD_AFTER_OPTIONS, moodAfter, setMoodAfter)}
              </div>

              <div className="mt-5">
                <Button stretched onClick={() => setStep(4)}>
                  Далее
                </Button>
              </div>
            </div>
          </Section>
        ) : null}

        {step === 4 ? (
          <Section header="4. Ваши теги (до 5)">
            <div className="px-3 py-3">
              <div className="flex flex-col gap-2 sm:flex-row">
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
                      className="rounded-xl border border-(--tgui--divider_color) bg-(--tgui--secondary_bg_color) px-3 py-1 text-xs text-(--tgui--text_color)"
                      onClick={() => removeTag(tag)}
                      title="Удалить тег"
                    >
                      {tag} ×
                    </button>
                  ))}
                </div>
              ) : (
                <p className="mt-3 text-sm text-(--tgui--hint_color)">Добавьте пару слов о впечатлении.</p>
              )}
              <div className="mt-5">
                <Button stretched onClick={() => setStep(5)}>
                  Далее
                </Button>
              </div>
            </div>
          </Section>
        ) : null}

        {step === 5 ? (
          <Section header="5. Поделиться карточкой">
            <div className="px-3 py-3">
              <div className="filmony-text-panel">
                <Title level="3" weight="2">
                  Скоро здесь будет больше
                </Title>
                <p className="mt-2 text-sm text-(--tgui--hint_color)">
                  На этом шаге позже можно будет отправлять карточку подписчикам и друзьям.
                </p>
              </div>
              <div className="mt-5">
                <Button stretched disabled={film == null || submitLoading} onClick={() => void handleSubmit()}>
                  {submitLoading ? 'Создаем...' : 'Готово'}
                </Button>
              </div>
            </div>
          </Section>
        ) : null}

        {error != null ? (
          <div className="mt-4 rounded-xl border border-(--tgui--destructive_text_color) bg-[color-mix(in_srgb,var(--tgui--destructive_text_color)_10%,transparent)] px-3 py-2">
            <p className="text-sm text-(--tgui--destructive_text_color)">{error}</p>
          </div>
        ) : null}
      </main>
    </div>
  )
}
