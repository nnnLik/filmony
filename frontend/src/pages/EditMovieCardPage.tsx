import { Button, Input, Section } from '@telegram-apps/telegram-ui'
import { useEffect, useMemo, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'

import { getMovieCardById, updateMovieCard } from '../api/cardApi'
import { ApiError, formatApiDetail } from '../api/client'
import { getMyProfile } from '../api/profileApi'
import type { CardCompany, CardMoodAfter, CardMoodBefore, MovieCard } from '../api/profileTypes'
import { clearMyProfileBundleCache, readMyProfileBundleCache } from '../lib/myProfileBundleCache'

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

function normalizeRating(value: number): number {
  const clamped = Math.max(1, Math.min(10, value))
  return Math.round(clamped * 2) / 2
}

function formatRating(value: number): string {
  return Number.isInteger(value) ? String(value) : value.toFixed(1)
}

export function EditMovieCardPage() {
  const navigate = useNavigate()
  const { cardId } = useParams<{ cardId?: string }>()
  const [viewerId, setViewerId] = useState<string | null>(() => readMyProfileBundleCache()?.profile.id ?? null)
  const [card, setCard] = useState<MovieCard | null>(null)
  const [loading, setLoading] = useState(false)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const [rating, setRating] = useState(7.5)
  const [company, setCompany] = useState<CardCompany>('alone')
  const [moodBefore, setMoodBefore] = useState<CardMoodBefore>('relax')
  const [moodAfter, setMoodAfter] = useState<CardMoodAfter>('enjoyed')
  const [customTags, setCustomTags] = useState<string[]>([])
  const [tagInput, setTagInput] = useState('')

  const parsedCardId = useMemo(() => {
    if (cardId == null) return null
    const value = Number(cardId)
    return Number.isInteger(value) && value > 0 ? value : null
  }, [cardId])

  const isOwner =
    card != null && card.user_id != null && viewerId != null && card.user_id === viewerId

  useEffect(() => {
    if (viewerId != null) return
    let alive = true
    void (async () => {
      try {
        const profile = await getMyProfile()
        if (!alive) return
        setViewerId(profile.id)
      } catch {
        // no-op: owner check will fail closed
      }
    })()
    return () => {
      alive = false
    }
  }, [viewerId])

  useEffect(() => {
    if (parsedCardId == null) return
    let alive = true
    void (async () => {
      setLoading(true)
      setError(null)
      try {
        const item = await getMovieCardById(parsedCardId)
        if (!alive) return
        setCard(item)
        setRating(item.rating)
        setCompany(item.company)
        setMoodBefore(item.mood_before)
        setMoodAfter(item.mood_after)
        setCustomTags(item.custom_tags)
      } catch (e) {
        if (!alive) return
        if (e instanceof ApiError) {
          setError(formatApiDetail(e.detail))
        } else {
          setError('Не удалось загрузить карточку')
        }
      } finally {
        if (alive) setLoading(false)
      }
    })()
    return () => {
      alive = false
    }
  }, [parsedCardId])

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

  function addTag() {
    const trimmed = tagInput.trim()
    if (trimmed === '') return
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

  async function handleSave() {
    if (parsedCardId == null || saving) return
    setSaving(true)
    setError(null)
    try {
      await updateMovieCard(parsedCardId, {
        rating: normalizeRating(rating),
        company,
        mood_before: moodBefore,
        mood_after: moodAfter,
        custom_tags: customTags,
      })
      clearMyProfileBundleCache()
      // Pop edit off the history stack instead of pushing another detail route.
      // Otherwise "back" from detail returns to edit (detail → edit → detail push).
      void navigate(-1)
    } catch (e) {
      if (e instanceof ApiError) {
        setError(formatApiDetail(e.detail))
      } else {
        setError('Не удалось сохранить карточку')
      }
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="min-h-full">
      <header className="sticky top-0 z-20 border-b border-(--tgui--divider_color) bg-[color-mix(in_srgb,var(--tgui--bg_color)_88%,transparent)] backdrop-blur-md">
        <div className="flex items-center justify-between px-4 pb-2 pt-3">
          <button
            type="button"
            onClick={() => {
              if (parsedCardId == null) {
                void navigate('/profile')
                return
              }
              void navigate(-1)
            }}
            className="flex h-10 w-10 items-center justify-center rounded-xl text-lg text-(--tgui--link_color) active:opacity-70"
            aria-label="Назад"
          >
            ←
          </button>
          <h1 className="text-base font-semibold tracking-tight text-(--tgui--text_color)">Редактирование карточки</h1>
          <span className="w-10" />
        </div>
      </header>

      <main className="mx-auto max-w-md px-4 py-4">
        {parsedCardId == null ? (
          <div className="py-10 text-center">
            <p className="filmony-text-panel text-sm text-(--tgui--destructive_text_color)">Некорректный id карточки</p>
            <Link to="/profile" className="mt-3 inline-block text-sm text-(--tgui--link_color)">
              Вернуться в профиль
            </Link>
          </div>
        ) : null}

        {loading ? <p className="filmony-text-panel py-10 text-center text-sm text-(--tgui--hint_color)">Загрузка…</p> : null}

        {!loading && card != null && !isOwner ? (
          <div className="py-10 text-center">
            <p className="filmony-text-panel text-sm text-(--tgui--destructive_text_color)">
              Редактировать карточку может только ее владелец
            </p>
            <Link to={`/cards/${card.id}`} className="mt-3 inline-block text-sm text-(--tgui--link_color)">
              Вернуться к карточке
            </Link>
          </div>
        ) : null}

        {!loading && card != null && isOwner ? (
          <div className="space-y-4">
            <Section header="Оценка">
              <div className="px-3 py-3 text-center">
                <p className="text-sm text-(--tgui--hint_color)">Текущая оценка</p>
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
            </Section>

            <Section header="Контекст просмотра">
              <div className="px-3 py-3">
                <p className="text-sm font-medium text-(--tgui--text_color)">С кем смотрели:</p>
                {renderChoiceChips(COMPANY_OPTIONS, company, setCompany)}
                <p className="mt-4 text-sm font-medium text-(--tgui--text_color)">До просмотра:</p>
                {renderChoiceChips(MOOD_BEFORE_OPTIONS, moodBefore, setMoodBefore)}
                <p className="mt-4 text-sm font-medium text-(--tgui--text_color)">После просмотра:</p>
                {renderChoiceChips(MOOD_AFTER_OPTIONS, moodAfter, setMoodAfter)}
              </div>
            </Section>

            <Section header="Свои теги (до 5)">
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
              </div>
            </Section>

            <Button stretched disabled={saving} onClick={() => void handleSave()}>
              {saving ? 'Сохраняем...' : 'Сохранить'}
            </Button>
          </div>
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
