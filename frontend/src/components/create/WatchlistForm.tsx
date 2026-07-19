import { Button, Title } from '@telegram-apps/telegram-ui'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { useCallback, useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'

import { resolveFilmByKinopoiskUrl } from '../../api/cardApi'
import { ApiError, formatApiDetail } from '../../api/client'
import {
  isLikelyUrl,
  resolveCatalogByUrl,
  type CatalogCandidate,
} from '../../api/catalogApi'
import {
  createMyCardCategory,
  getMyCardCategories,
  getMyProfile,
  getUserSubscriptions,
  patchMyWatchlistEntry,
  postCreateWatchlistEntry,
  type PatchWatchlistEntryBody,
  type WatchTag,
} from '../../api/profileApi'
import type { CardCompany, Film, SubscriptionListItem } from '../../api/profileTypes'
import { CommentDraftMultiline } from '../comments/CommentDraftMirrorField'
import { CommentSpoilerToggleButton } from '../comments/CommentSpoilerToggleButton'
import { FilmGenreChips } from '../films/FilmGenreChips'
import { MutualWatchFriendsMultiPicker } from '../watchlist/MutualWatchFriendsMultiPicker'
import { myCardCategoriesQueryKey } from '../../feed/feedQueryKeys'
import { useCatalogCandidates } from '../../hooks/useCatalogCandidates'
import { createManualBinding, bindingFromResolveByUrl, mapResolveError } from '../../lib/createCardBinding'
import { clearMyProfileBundleCache } from '../../lib/myProfileBundleCache'
import { filterMutualSubscriptions } from '../../lib/mutualSubscriptionFilter'
import { toggleSpoilerAtSelection } from '../../lib/spoilerTokens'
import { MAX_WATCH_NOTE_LEN } from '../../lib/watchNoteLimits'
import { safeHapticSuccess } from '../../lib/safeHaptic'
import {
  buildWatchlistCreatePayload,
  watchlistBindingPreview,
  type WatchlistBinding,
} from '../../lib/watchlistBinding'

const WATCHLIST_COMPANY_OPTIONS: Array<{ value: CardCompany; label: string }> = [
  { value: 'alone', label: 'Один' },
  { value: 'partner', label: 'С партнером' },
  { value: 'friends', label: 'С друзьями' },
  { value: 'family', label: 'С семьей' },
]

const CHIP_COLORS = [
  'bg-[#3B82F633] text-[#60A5FA]',
  'bg-[#F9731633] text-[#FDBA74]',
  'bg-[#22C55E33] text-[#86EFAC]',
  'bg-[#A855F733] text-[#D8B4FE]',
  'bg-[#EC489933] text-[#F9A8D4]',
] as const

const TEXT_FIELD_CLASS =
  'w-full min-h-11 rounded-xl border border-(--tgui--divider_color) bg-(--tgui--bg_color) px-3 py-2.5 text-sm text-(--tgui--text_color) outline-none transition-[border-color,box-shadow] placeholder:text-(--tgui--hint_color) focus-visible:border-(--tgui--link_color) focus-visible:ring-2 focus-visible:ring-[color-mix(in_srgb,var(--tgui--link_color)_32%,transparent)]'

async function hydrateKinopoiskCatalogFilm(externalId: string): Promise<Film> {
  const id = externalId.trim()
  try {
    return await resolveFilmByKinopoiskUrl(`https://www.kinopoisk.ru/film/${id}/`)
  } catch (firstErr) {
    try {
      return await resolveFilmByKinopoiskUrl(`https://www.kinopoisk.ru/series/${id}/`)
    } catch {
      throw firstErr
    }
  }
}

async function candidateToBinding(candidate: CatalogCandidate): Promise<WatchlistBinding | null> {
  if (candidate.catalog_item_id == null) return null
  if (candidate.kind === 'film' && candidate.provider === 'kinopoisk') {
    const film = await hydrateKinopoiskCatalogFilm(candidate.external_id)
    return {
      kind: 'catalog_film',
      catalogItemId: candidate.catalog_item_id,
      film,
    }
  }
  if (candidate.kind === 'game') {
    return {
      kind: 'catalog_game',
      catalogItemId: candidate.catalog_item_id,
      display_title: candidate.title,
      display_cover_url: candidate.cover_url,
      display_summary: null,
      subtitle: candidate.subtitle,
    }
  }
  return { kind: 'catalog_item', catalogItemId: candidate.catalog_item_id }
}

function renderChoiceChips<T extends string>(
  options: Array<{ value: T; label: string }>,
  selected: T,
  onSelect: (value: T) => void,
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

export type WatchlistFormEditMode = {
  entryId: number
  cardId: number
}

export type WatchlistFormProps = {
  binding: WatchlistBinding | null
  onBindingChange?: (binding: WatchlistBinding | null) => void
  /** When true, user cannot change the selected title/source. */
  lockBinding?: boolean
  editMode?: WatchlistFormEditMode
  initialCompany?: CardCompany
  initialShelfId?: number | null
  initialNote?: string
  initialWatchWithUserIds?: string[]
}

export function WatchlistForm({
  binding,
  onBindingChange,
  lockBinding = false,
  editMode,
  initialCompany = 'alone',
  initialShelfId = null,
  initialNote = '',
  initialWatchWithUserIds = [],
}: WatchlistFormProps) {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const isEditMode = editMode != null

  const [searchDraft, setSearchDraft] = useState('')
  const [resolveBusy, setResolveBusy] = useState(false)
  const [resolveError, setResolveError] = useState<string | null>(null)
  const [manualMode, setManualMode] = useState(false)
  const [manualTitle, setManualTitle] = useState('')
  const [manualCoverUrl, setManualCoverUrl] = useState('')

  const [watchlistBusy, setWatchlistBusy] = useState(false)
  const [watchlistError, setWatchlistError] = useState<string | null>(null)
  const [watchlistTag] = useState<WatchTag>('watch_later')
  const [watchWithUserIds, setWatchWithUserIds] = useState<string[]>(initialWatchWithUserIds)
  const [watchlistCompany, setWatchlistCompany] = useState<CardCompany>(initialCompany)
  const [watchlistShelfId, setWatchlistShelfId] = useState<number | null>(initialShelfId)
  const [watchlistNote, setWatchlistNote] = useState(initialNote)
  const [mutualFriends, setMutualFriends] = useState<SubscriptionListItem[]>([])
  const [mutualFriendsLoading, setMutualFriendsLoading] = useState(false)
  const [shelfError, setShelfError] = useState<string | null>(null)
  const [shelfCreateExpanded, setShelfCreateExpanded] = useState(false)
  const [newShelfDraft, setNewShelfDraft] = useState('')
  const [createShelfBusy, setCreateShelfBusy] = useState(false)

  const watchlistNoteRef = useRef<HTMLTextAreaElement>(null)

  const urlLike = isLikelyUrl(searchDraft)
  const candidatesQuery = useCatalogCandidates(searchDraft, {
    enabled: !isEditMode && binding == null && !manualMode && !urlLike,
  })

  const shelvesQuery = useQuery({
    queryKey: myCardCategoriesQueryKey(),
    queryFn: getMyCardCategories,
    staleTime: 60_000,
    gcTime: 30 * 60_000,
  })

  useEffect(() => {
    let alive = true
    void (async () => {
      setMutualFriendsLoading(true)
      try {
        const me = await getMyProfile()
        if (!alive) return
        const subs = await getUserSubscriptions(me.id, 'both')
        if (!alive) return
        setMutualFriends(filterMutualSubscriptions(subs.items))
      } catch {
        if (!alive) return
        setMutualFriends([])
      } finally {
        if (alive) setMutualFriendsLoading(false)
      }
    })()
    return () => {
      alive = false
    }
  }, [])

  const watchlistNoteTooLong = watchlistNote.length > MAX_WATCH_NOTE_LEN
  const preview = binding != null ? watchlistBindingPreview(binding) : null

  const toggleSpoilerInWatchlistNote = useCallback(() => {
    const el = watchlistNoteRef.current
    const toggled = toggleSpoilerAtSelection(
      watchlistNote,
      el?.selectionStart ?? null,
      el?.selectionEnd ?? null,
      MAX_WATCH_NOTE_LEN,
    )
    if (toggled == null) return
    setWatchlistNote(toggled.nextValue)
    window.requestAnimationFrame(() => {
      const target = watchlistNoteRef.current
      if (!target) return
      target.focus()
      target.setSelectionRange(toggled.caret, toggled.caret)
    })
  }, [watchlistNote])

  function toggleWatchWithUser(userId: string) {
    setWatchWithUserIds((prev) =>
      prev.includes(userId) ? prev.filter((id) => id !== userId) : [...prev, userId],
    )
  }

  async function submitNewShelf() {
    const name = newShelfDraft.trim()
    if (name === '') {
      setShelfError('Введите название полки')
      return
    }
    setCreateShelfBusy(true)
    setShelfError(null)
    try {
      const row = await createMyCardCategory({ name })
      setNewShelfDraft('')
      setWatchlistShelfId(row.id)
      setShelfCreateExpanded(false)
      void queryClient.invalidateQueries({ queryKey: myCardCategoriesQueryKey() })
      safeHapticSuccess()
    } catch (e) {
      if (e instanceof ApiError) {
        setShelfError(formatApiDetail(e.detail))
      } else {
        setShelfError('Не удалось создать полку')
      }
    } finally {
      setCreateShelfBusy(false)
    }
  }

  async function handleResolveUrl() {
    const url = searchDraft.trim()
    if (url === '') return
    setResolveBusy(true)
    setResolveError(null)
    try {
      const resolved = await resolveCatalogByUrl(url)
      onBindingChange?.(bindingFromResolveByUrl(resolved))
      setSearchDraft('')
    } catch (e) {
      if (e instanceof ApiError) {
        setResolveError(mapResolveError(formatApiDetail(e.detail)))
      } else {
        setResolveError('Не удалось распознать ссылку')
      }
    } finally {
      setResolveBusy(false)
    }
  }

  function handleManualContinue() {
    const title = manualTitle.trim()
    if (title === '') {
      setResolveError('Введите название')
      return
    }
    const cover = manualCoverUrl.trim()
    onBindingChange?.(createManualBinding(title, cover === '' ? null : cover))
    setManualMode(false)
    setResolveError(null)
  }

  async function handleSubmit() {
    if (isEditMode) {
      await handleSaveEdit()
      return
    }
    if (binding == null) return
    const payload = buildWatchlistCreatePayload(binding, {
      watch_tag: watchlistTag,
      company: watchlistCompany,
      category_id: watchlistShelfId,
      watch_note: watchlistNote,
      watch_with_user_ids: watchlistCompany === 'alone' ? [] : watchWithUserIds,
    })
    if (payload == null) return
    setWatchlistBusy(true)
    setWatchlistError(null)
    try {
      await postCreateWatchlistEntry(payload)
      clearMyProfileBundleCache()
      void queryClient.invalidateQueries({ queryKey: ['userWatchlist'] })
      safeHapticSuccess()
      void navigate('/profile', { replace: true, state: { moviesSegment: 'watchlist' as const } })
    } catch (e) {
      if (e instanceof ApiError) {
        if (e.status === 409) {
          setWatchlistError('Эта тема уже в списке «Позже».')
          return
        }
        const msg = formatApiDetail(e.detail).toLowerCase()
        if (msg.includes('movie card already exists')) {
          setWatchlistError('У вас уже есть оценённая карточка для этой темы.')
          return
        }
        setWatchlistError(formatApiDetail(e.detail))
      } else {
        setWatchlistError('Не удалось добавить в список')
      }
    } finally {
      setWatchlistBusy(false)
    }
  }

  async function handleSaveEdit() {
    if (editMode == null) return
    const body: PatchWatchlistEntryBody = {
      company: watchlistCompany,
      watch_note: watchlistNote.trim().slice(0, MAX_WATCH_NOTE_LEN),
      watch_with_user_ids: watchlistCompany === 'alone' ? [] : watchWithUserIds,
    }
    if (watchlistShelfId != null && watchlistShelfId > 0) {
      body.category_id = watchlistShelfId
    }
    setWatchlistBusy(true)
    setWatchlistError(null)
    try {
      await patchMyWatchlistEntry(editMode.entryId, body)
      clearMyProfileBundleCache()
      void queryClient.invalidateQueries({ queryKey: ['userWatchlist'] })
      safeHapticSuccess()
      void navigate(`/cards/${editMode.cardId}`, { replace: true })
    } catch (e) {
      if (e instanceof ApiError) {
        setWatchlistError(formatApiDetail(e.detail))
      } else {
        setWatchlistError('Не удалось сохранить изменения')
      }
    } finally {
      setWatchlistBusy(false)
    }
  }

  const candidateItems = candidatesQuery.data?.items ?? []

  return (
    <div className="space-y-4">
      {!isEditMode && binding == null ? (
        <section className="overflow-hidden rounded-2xl border border-(--tgui--divider_color) bg-(--tgui--secondary_bg_color)">
          <div className="border-b border-(--tgui--divider_color) px-4 py-3">
            <h2 className="text-[15px] font-semibold tracking-tight text-(--tgui--text_color)">
              Что добавить в «Позже»
            </h2>
          </div>
          <div className="p-4">
            {!manualMode ? (
              <>
                <label htmlFor="watchlist-smart-field" className="sr-only">
                  Поиск или ссылка
                </label>
                <input
                  id="watchlist-smart-field"
                  type="text"
                  placeholder="Название, игра или ссылка Кинопоиска / YouTube…"
                  value={searchDraft}
                  onChange={(e) => {
                    setSearchDraft(e.currentTarget.value)
                    setResolveError(null)
                  }}
                  className={TEXT_FIELD_CLASS}
                  autoComplete="off"
                />
                {urlLike ? (
                  <div className="mt-3">
                    <Button stretched disabled={resolveBusy} onClick={() => void handleResolveUrl()}>
                      {resolveBusy ? 'Проверяем ссылку…' : 'Открыть по ссылке'}
                    </Button>
                  </div>
                ) : null}
                {!urlLike && searchDraft.trim().length >= 3 ? (
                  <div className="mt-3 space-y-2">
                    {candidatesQuery.isLoading ? (
                      <p className="text-xs text-(--tgui--hint_color)">Ищем…</p>
                    ) : null}
                    {candidateItems.map((hit) => {
                      const selectable = hit.catalog_item_id != null
                      return (
                        <button
                          key={hit.candidate_id}
                          type="button"
                          disabled={!selectable || resolveBusy}
                          onClick={() => {
                            void (async () => {
                              setResolveBusy(true)
                              setResolveError(null)
                              try {
                                const next = await candidateToBinding(hit)
                                if (next == null) {
                                  setResolveError('У результата нет привязки к каталогу')
                                  return
                                }
                                onBindingChange?.(next)
                                setSearchDraft('')
                              } catch (e) {
                                if (e instanceof ApiError) {
                                  setResolveError(formatApiDetail(e.detail))
                                } else {
                                  setResolveError('Не удалось выбрать запись из каталога')
                                }
                              } finally {
                                setResolveBusy(false)
                              }
                            })()
                          }}
                          className="flex w-full gap-3 rounded-xl border border-(--tgui--divider_color) bg-(--tgui--bg_color) p-3 text-left active:opacity-90 disabled:opacity-50"
                        >
                          <div className="h-16 w-11 shrink-0 overflow-hidden rounded-lg bg-(--tgui--secondary_bg_color)">
                            {hit.cover_url ? (
                              <img
                                src={hit.cover_url}
                                alt=""
                                className="h-full w-full object-cover"
                              />
                            ) : (
                              <div className="flex h-full w-full items-center justify-center text-[9px] text-(--tgui--hint_color)">
                                —
                              </div>
                            )}
                          </div>
                          <div className="min-w-0 flex-1">
                            <p className="truncate text-sm font-medium text-(--tgui--text_color)">
                              {hit.title}
                            </p>
                            {hit.subtitle ? (
                              <p className="truncate text-xs text-(--tgui--hint_color)">{hit.subtitle}</p>
                            ) : null}
                          </div>
                        </button>
                      )
                    })}
                  </div>
                ) : null}
                <button
                  type="button"
                  className="mt-4 text-sm font-medium text-(--tgui--link_color) active:opacity-80"
                  onClick={() => {
                    setManualMode(true)
                    setResolveError(null)
                  }}
                >
                  Создать вручную
                </button>
              </>
            ) : (
              <>
                <label htmlFor="watchlist-manual-title" className="text-sm font-medium text-(--tgui--text_color)">
                  Название
                </label>
                <input
                  id="watchlist-manual-title"
                  type="text"
                  value={manualTitle}
                  onChange={(e) => setManualTitle(e.currentTarget.value)}
                  className={`mt-2 ${TEXT_FIELD_CLASS}`}
                  placeholder="Например: фильм, которого нет в каталоге"
                />
                <label
                  htmlFor="watchlist-manual-cover"
                  className="mt-4 block text-sm font-medium text-(--tgui--text_color)"
                >
                  Обложка (URL, необязательно)
                </label>
                <input
                  id="watchlist-manual-cover"
                  type="url"
                  value={manualCoverUrl}
                  onChange={(e) => setManualCoverUrl(e.currentTarget.value)}
                  className={`mt-2 ${TEXT_FIELD_CLASS}`}
                  placeholder="https://…"
                />
                <div className="mt-4 flex flex-col gap-2">
                  <Button stretched onClick={() => handleManualContinue()}>
                    Дальше
                  </Button>
                  <Button
                    mode="gray"
                    stretched
                    onClick={() => {
                      setManualMode(false)
                      setManualTitle('')
                      setManualCoverUrl('')
                    }}
                  >
                    Назад к поиску
                  </Button>
                </div>
              </>
            )}
            {resolveError != null ? (
              <p className="mt-3 text-sm text-(--tgui--destructive_text_color)">{resolveError}</p>
            ) : null}
          </div>
        </section>
      ) : null}

      {(binding != null || isEditMode) && preview != null ? (
        <section className="overflow-hidden rounded-2xl border border-(--tgui--divider_color) bg-(--tgui--secondary_bg_color)">
          <div className="border-b border-(--tgui--divider_color) px-4 py-3">
            <h2 className="text-[15px] font-semibold tracking-tight text-(--tgui--text_color)">
              {isEditMode ? 'Редактировать «Позже»' : 'Детали для «Позже»'}
            </h2>
          </div>
          <div className="p-4">
            <div className="filmony-text-panel flex gap-3 rounded-xl border border-(--tgui--divider_color) bg-(--tgui--bg_color) p-3">
              <div className="h-28 w-[4.5rem] shrink-0 overflow-hidden rounded-lg bg-(--tgui--secondary_bg_color)">
                {preview.posterUrl ? (
                  <img src={preview.posterUrl} alt={preview.title} className="h-full w-full object-cover" />
                ) : (
                  <div className="flex h-full w-full items-center justify-center px-1 text-center text-[10px] text-(--tgui--hint_color)">
                    Нет обложки
                  </div>
                )}
              </div>
              <div className="min-w-0 flex-1">
                <Title level="3" weight="2">
                  {preview.title}
                </Title>
                <p className="mt-1 text-sm text-(--tgui--hint_color)">{preview.yearLabel}</p>
                <FilmGenreChips genres={preview.genres} size="md" maxVisible={6} className="mt-2" />
              </div>
            </div>

            {!lockBinding && !isEditMode ? (
              <div className="mt-3">
                <Button
                  mode="gray"
                  stretched
                  onClick={() => {
                    onBindingChange?.(null)
                    setWatchlistError(null)
                  }}
                >
                  Изменить тему
                </Button>
              </div>
            ) : null}

            <div className="filmony-text-panel mt-5">
              <div>
                <p className="text-sm font-medium text-(--tgui--text_color)">С кем планируете смотреть</p>
                {renderChoiceChips(WATCHLIST_COMPANY_OPTIONS, watchlistCompany, (value) => {
                  setWatchlistCompany(value)
                  if (value === 'alone') {
                    setWatchWithUserIds([])
                  }
                })}
              </div>

              {watchlistCompany !== 'alone' ? (
                <div className="mt-5 border-t border-(--tgui--divider_color) pt-5">
                  <MutualWatchFriendsMultiPicker
                    friends={mutualFriends}
                    loading={mutualFriendsLoading}
                    selectedUserIds={watchWithUserIds}
                    onToggle={toggleWatchWithUser}
                  />
                </div>
              ) : null}

              <div className="mt-5 border-t border-(--tgui--divider_color) pt-5">
                <p className="text-sm font-medium text-(--tgui--text_color)">Полка в коллекции</p>
                <p className="mt-1 text-xs text-(--tgui--hint_color)">
                  Можно оставить автоматическую полку или выбрать свою.
                </p>
                {shelvesQuery.isLoading ? (
                  <p className="mt-2 text-xs text-(--tgui--hint_color)">Загрузка полок…</p>
                ) : shelvesQuery.isError ? (
                  <p className="filmony-text-panel mt-2 text-xs text-(--tgui--hint_color)">
                    Полки временно недоступны — сервер подставит полку по умолчанию.
                  </p>
                ) : (
                  <>
                    <label htmlFor="watchlist-shelf" className="sr-only">
                      Полка коллекции
                    </label>
                    <select
                      id="watchlist-shelf"
                      className={`mt-3 ${TEXT_FIELD_CLASS}`}
                      value={watchlistShelfId === null ? '' : String(watchlistShelfId)}
                      onChange={(e) => {
                        const raw = e.currentTarget.value
                        setWatchlistShelfId(raw === '' ? null : Number(raw))
                        setShelfError(null)
                      }}
                    >
                      <option value="">Авто (полка по умолчанию)</option>
                      {(shelvesQuery.data?.items ?? []).map((row) => (
                        <option key={row.id} value={String(row.id)}>
                          {row.name}
                        </option>
                      ))}
                    </select>
                    <div className="mt-2">
                      <button
                        type="button"
                        className="text-sm font-medium text-(--tgui--link_color) active:opacity-80"
                        onClick={() => {
                          setShelfCreateExpanded((v) => !v)
                          setShelfError(null)
                        }}
                      >
                        {shelfCreateExpanded ? 'Скрыть создание полки' : '+ Новая полка'}
                      </button>
                      {shelfCreateExpanded ? (
                        <div className="mt-2 rounded-xl border border-(--tgui--divider_color) bg-(--tgui--bg_color) p-3">
                          <div className="mt-2 flex flex-col gap-2 sm:flex-row sm:items-stretch">
                            <input
                              type="text"
                              maxLength={120}
                              placeholder="Например: Триллеры 2025"
                              autoComplete="off"
                              value={newShelfDraft}
                              onChange={(e) => {
                                setNewShelfDraft(e.currentTarget.value)
                                setShelfError(null)
                              }}
                              className={`min-w-0 flex-1 ${TEXT_FIELD_CLASS}`}
                            />
                            <Button
                              mode="gray"
                              className="shrink-0 sm:self-stretch"
                              disabled={createShelfBusy}
                              type="button"
                              onClick={() => void submitNewShelf()}
                            >
                              {createShelfBusy ? '…' : 'Создать'}
                            </Button>
                          </div>
                          {shelfError != null ? (
                            <p className="mt-2 text-xs text-(--tgui--destructive_text_color)">{shelfError}</p>
                          ) : null}
                        </div>
                      ) : null}
                    </div>
                  </>
                )}
              </div>

              <div className="mt-6 border-t border-(--tgui--divider_color) pt-5">
                <p className="text-sm font-medium text-(--tgui--text_color)">Заметка</p>
                <p className="mt-1 text-xs text-(--tgui--hint_color)">
                  По желанию — до {MAX_WATCH_NOTE_LEN} символов. Перенесётся, когда поставите оценку.
                </p>
                <div className="mt-2 flex gap-2">
                  <CommentDraftMultiline
                    ref={watchlistNoteRef}
                    value={watchlistNote}
                    onChange={(v) => {
                      setWatchlistNote(v)
                      setWatchlistError(null)
                    }}
                    placeholder="Например: посмотреть в выходные с друзьями…"
                    ariaLabel="Заметка для списка «Позже»"
                    maxLength={MAX_WATCH_NOTE_LEN}
                    rows={4}
                    wrapperClassName={`min-h-24 flex-1 ${TEXT_FIELD_CLASS}`}
                  />
                  <div className="flex shrink-0 flex-col justify-start pt-1">
                    <CommentSpoilerToggleButton
                      allowInsert={watchlistNote.length < MAX_WATCH_NOTE_LEN}
                      onToggleSpoiler={toggleSpoilerInWatchlistNote}
                    />
                  </div>
                </div>
                {watchlistNoteTooLong ? (
                  <p className="mt-1 text-xs text-(--tgui--destructive_text_color)">
                    Не больше {MAX_WATCH_NOTE_LEN} символов
                  </p>
                ) : (
                  <p className="mt-1 text-xs text-(--tgui--hint_color)">
                    {watchlistNote.length}/{MAX_WATCH_NOTE_LEN}
                  </p>
                )}
              </div>

              {watchlistError != null ? (
                <p className="mt-4 text-sm text-(--tgui--destructive_text_color)">{watchlistError}</p>
              ) : null}

              <div className="mt-5 flex flex-col gap-2">
                <Button
                  stretched
                  disabled={watchlistBusy || watchlistNoteTooLong}
                  onClick={() => void handleSubmit()}
                >
                  {watchlistBusy
                    ? isEditMode
                      ? 'Сохраняем…'
                      : 'Добавляем…'
                    : isEditMode
                      ? 'Сохранить'
                      : 'Добавить в «Позже»'}
                </Button>
              </div>
            </div>
          </div>
        </section>
      ) : null}
    </div>
  )
}
