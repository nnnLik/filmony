import { Button, Section } from '@telegram-apps/telegram-ui'
import { useQuery } from '@tanstack/react-query'
import { useCallback, useEffect, useMemo, useRef, useState, type ChangeEvent } from 'react'
import { useNavigate, useParams } from 'react-router'

import { getMovieCardById, updateMovieCard, uploadUserCardAudio, deleteUserCardAudio } from '../api/cardApi'
import { ApiError, formatApiDetail } from '../api/client'
import { getMyCardCategories, getMyProfile } from '../api/profileApi'
import type { CardCompany, CardMoodAfter, CardMoodBefore, MovieCard, MyUserCardCategory } from '../api/profileTypes'
import { CardFormFields } from '../components/create/CardFormFields'
import { PageErrorState } from '../components/ui/PageErrorState'
import { PageLoadingState } from '../components/ui/PageLoadingState'
import { clearMyProfileBundleCache, readMyProfileBundleCache } from '../lib/myProfileBundleCache'
import { myCardCategoriesQueryKey } from '../feed/feedQueryKeys'
import { MAX_CUSTOM_TAG_LEN, normalizeRating } from '../lib/createCardBinding'

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
  const [watchNote, setWatchNote] = useState('')
  /** Полка после загрузки списка категорий; в PATCH уходит только при успешной загрузке списка. */
  const [draftCategoryId, setDraftCategoryId] = useState<number | null>(null)
  const audioFileInputRef = useRef<HTMLInputElement>(null)

  const [audioUrl, setAudioUrl] = useState<string | null>(null)
  const [audioBusy, setAudioBusy] = useState(false)

  const shelvesQuery = useQuery({
    queryKey: myCardCategoriesQueryKey(),
    queryFn: getMyCardCategories,
    staleTime: 60_000,
    gcTime: 30 * 60_000,
  })

  const shelfRows: MyUserCardCategory[] = useMemo(() => {
    const base = shelvesQuery.data?.items ?? []
    const curId = card?.category?.id
    const curNameRaw = typeof card?.category?.name === 'string' ? card.category.name.trim() : ''
    if (typeof curId === 'number' && curId >= 1 && curNameRaw !== '' && !base.some((r) => r.id === curId)) {
      return [...base, { id: curId, name: curNameRaw, created_at: '' }]
    }
    return base
  }, [card, shelvesQuery.data?.items])

  const shelfSelectBusy = shelvesQuery.isLoading && shelfRows.length === 0

  const shelfSelectControlId = useMemo(() => {
    if (
      draftCategoryId != null &&
      draftCategoryId >= 1 &&
      shelfRows.some((r) => r.id === draftCategoryId)
    ) {
      return draftCategoryId
    }
    const fallback = shelfRows[0]?.id
    return typeof fallback === 'number' && fallback >= 1 ? fallback : null
  }, [draftCategoryId, shelfRows])

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
        if (item.is_planned === true) {
          void navigate(`/cards/${parsedCardId}/edit-planned`, { replace: true })
          return
        }
        setCard(item)
        setRating(item.rating)
        setCompany(item.company)
        setMoodBefore(item.mood_before)
        setMoodAfter(item.mood_after)
        setCustomTags(item.custom_tags)
        setWatchNote(item.watch_note ?? '')
        const cid = item.category?.id
        setDraftCategoryId(typeof cid === 'number' && cid >= 1 ? cid : null)
        const au = item.audio_url
        setAudioUrl(typeof au === 'string' && au.trim() !== '' ? au : null)
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
  }, [parsedCardId, navigate])

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
    if (trimmed.length > MAX_CUSTOM_TAG_LEN) {
      setError(`Тег не длиннее ${MAX_CUSTOM_TAG_LEN} символов`)
      return
    }
    setCustomTags((prev) => [...prev, trimmed])
    setTagInput('')
    setError(null)
  }

  function removeTag(tag: string) {
    setCustomTags((prev) => prev.filter((item) => item !== tag))
  }

  const handleAudioFileChange = useCallback(
    async (event: ChangeEvent<HTMLInputElement>) => {
      const file = event.target.files?.[0]
      event.target.value = ''
      if (file == null || parsedCardId == null) return
      setAudioBusy(true)
      setError(null)
      try {
        const { url } = await uploadUserCardAudio(parsedCardId, file)
        setAudioUrl(url)
      } catch (e) {
        if (e instanceof ApiError) {
          setError(formatApiDetail(e.detail))
        } else {
          setError('Не удалось загрузить аудио')
        }
      } finally {
        setAudioBusy(false)
      }
    },
    [parsedCardId],
  )

  const handleRemoveAudio = useCallback(async () => {
    if (parsedCardId == null || audioBusy) return
    setAudioBusy(true)
    setError(null)
    try {
      await deleteUserCardAudio(parsedCardId)
      setAudioUrl(null)
    } catch (e) {
      if (e instanceof ApiError) {
        setError(formatApiDetail(e.detail))
      } else {
        setError('Не удалось удалить аудио')
      }
    } finally {
      setAudioBusy(false)
    }
  }, [parsedCardId, audioBusy])

  async function handleSave() {
    if (parsedCardId == null || saving) return
    setSaving(true)
    setError(null)
    try {
      const shelfPatch =
        shelvesQuery.isSuccess && draftCategoryId != null && draftCategoryId >= 1
          ? { category_id: draftCategoryId }
          : {}
      await updateMovieCard(parsedCardId, {
        rating: normalizeRating(rating),
        company,
        mood_before: moodBefore,
        mood_after: moodAfter,
        custom_tags: customTags,
        watch_note: watchNote.trim(),
        ...shelfPatch,
      })
      clearMyProfileBundleCache()
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

  if (parsedCardId == null) {
    return (
      <PageErrorState
        message="Некорректный id карточки"
        backLabel="Вернуться в профиль"
        backHref="/profile"
      />
    )
  }

  if (loading) {
    return <PageLoadingState message="Загрузка…" className="bg-(--tgui--bg_color)" />
  }

  if (error != null && card == null) {
    return (
      <PageErrorState
        message={error}
        onRetry={() => {
          setLoading(true)
          setError(null)
          void getMovieCardById(parsedCardId)
            .then((item) => {
              if (item.is_planned === true) {
                void navigate(`/cards/${parsedCardId}/edit-planned`, { replace: true })
                return
              }
              setCard(item)
              setRating(item.rating)
              setCompany(item.company)
              setMoodBefore(item.mood_before)
              setMoodAfter(item.mood_after)
              setCustomTags(item.custom_tags)
              setWatchNote(item.watch_note ?? '')
              const cid = item.category?.id
              setDraftCategoryId(typeof cid === 'number' && cid >= 1 ? cid : null)
              const au = item.audio_url
              setAudioUrl(typeof au === 'string' && au.trim() !== '' ? au : null)
            })
            .catch((e) => {
              if (e instanceof ApiError) {
                setError(formatApiDetail(e.detail))
              } else {
                setError('Не удалось загрузить карточку')
              }
            })
            .finally(() => setLoading(false))
        }}
        backLabel="Вернуться в профиль"
        backHref="/profile"
      />
    )
  }

  if (card != null && !isOwner) {
    return (
      <PageErrorState
        message="Редактировать карточку может только ее владелец"
        backLabel="Вернуться к карточке"
        backHref={`/cards/${card.id}`}
      />
    )
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
        {!loading && card != null && isOwner ? (
          <div className="space-y-4">
            <CardFormFields
              variant="edit"
              rating={rating}
              onRatingChange={setRating}
              company={company}
              onCompanyChange={setCompany}
              moodBefore={moodBefore}
              onMoodBeforeChange={setMoodBefore}
              moodAfter={moodAfter}
              onMoodAfterChange={setMoodAfter}
              viewerUserId={viewerId}
              watchNote={watchNote}
              onWatchNoteChange={setWatchNote}
              watchNoteDisabled={saving}
              shelf={{
                mode: 'edit',
                shelfRows,
                shelfSelectControlId,
                onShelfChange: setDraftCategoryId,
                shelfSelectBusy,
                shelvesError: shelvesQuery.isError,
                currentShelfName: card.category?.name,
                disabled: saving,
              }}
              tags={{
                mode: 'edit',
                customTags,
                tagInput,
                onTagInputChange: setTagInput,
                onAddTag: addTag,
                onRemoveTag: removeTag,
                disabled: saving,
              }}
            />

            <Section header="Атмосфера (звук)">
              <div className="space-y-3 px-3 py-3">
                <p className="text-xs text-(--tgui--hint_color)">
                  MP3, M4A, OGG, WAV или WebM, до ~50 МБ. Файл сохраняется сразу после выбора.
                </p>
                <p className="text-xs text-(--tgui--text_color)">
                  {audioUrl != null && audioUrl.trim() !== '' ? 'Аудио прикреплено.' : 'Пока без звука.'}
                </p>
                <div className="flex flex-wrap gap-2">
                  <Button
                    mode="gray"
                    size="s"
                    disabled={saving || audioBusy}
                    onClick={() => audioFileInputRef.current?.click()}
                  >
                    {audioBusy ? 'Загрузка...' : audioUrl != null && audioUrl.trim() !== '' ? 'Заменить файл' : 'Загрузить аудио'}
                  </Button>
                  {audioUrl != null && audioUrl.trim() !== '' ? (
                    <Button mode="gray" size="s" disabled={saving || audioBusy} onClick={() => void handleRemoveAudio()}>
                      Удалить аудио
                    </Button>
                  ) : null}
                </div>
                <input
                  ref={audioFileInputRef}
                  type="file"
                  accept="audio/mpeg,audio/mp4,audio/ogg,audio/wav,audio/webm,.mp3,.m4a,.ogg,.wav,.webm"
                  className="hidden"
                  onChange={(e) => void handleAudioFileChange(e)}
                />
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
