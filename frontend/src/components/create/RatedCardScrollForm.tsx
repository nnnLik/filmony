import { Button } from '@telegram-apps/telegram-ui'
import { useQuery } from '@tanstack/react-query'
import { useMemo, useRef, useCallback, type ReactNode } from 'react'
import { useNavigate } from 'react-router-dom'

import type { CardCompany, CardMoodAfter, CardMoodBefore, MyMovieCardTagStatItem } from '../../api/profileTypes'
import { getMyPlannedCard } from '../../api/profileApi'
import { CommentDraftMultiline } from '../comments/CommentDraftMirrorField'
import { CommentReactionTokenPicker } from '../comments/CommentReactionTokenPicker'
import { CommentSpoilerToggleButton } from '../comments/CommentSpoilerToggleButton'
import { CardCoverBlock } from './CardCoverBlock'
import {
  CREATE_CARD_TEXT_FIELD_CLASS,
  MAX_CUSTOM_TAG_LEN,
  formatRating,
  normalizeRating,
  plannedCardLookupParams,
  type CreationBinding,
} from '../../lib/createCardBinding'
import { insertSnippetAtCaret, reactionTokenFromId } from '../../lib/commentReactionTokens'
import { toggleSpoilerAtSelection } from '../../lib/spoilerTokens'
import { MAX_WATCH_NOTE_LEN } from '../../lib/watchNoteLimits'

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

type ShelfRow = { id: number; name: string }

export type RatedCardScrollFormProps = {
  binding: CreationBinding
  remixFromCard?: boolean
  duplicateMyCardId?: number | null
  title: string
  onTitleChange: (value: string) => void
  summary: string
  onSummaryChange: (value: string) => void
  coverUrl: string | null
  onCoverUrlChange: (value: string | null) => void
  rating: number
  onRatingChange: (value: number) => void
  company: CardCompany
  onCompanyChange: (value: CardCompany) => void
  moodBefore: CardMoodBefore
  onMoodBeforeChange: (value: CardMoodBefore) => void
  moodAfter: CardMoodAfter
  onMoodAfterChange: (value: CardMoodAfter) => void
  selectedShelfId: number | null
  onSelectedShelfIdChange: (value: number | null) => void
  shelves: ShelfRow[]
  shelvesLoading: boolean
  shelvesError: boolean
  shelfCreateExpanded: boolean
  onShelfCreateExpandedChange: (value: boolean) => void
  newShelfDraft: string
  onNewShelfDraftChange: (value: string) => void
  shelfError: string | null
  createShelfBusy: boolean
  onCreateShelf: () => void
  customTags: string[]
  tagInput: string
  onTagInputChange: (value: string) => void
  tagFieldError: string | null
  onAddTag: () => void
  onAddTagFromSuggestion: (label: string) => void
  onRemoveTag: (tag: string) => void
  myTagStats: MyMovieCardTagStatItem[]
  watchNote: string
  onWatchNoteChange: (value: string) => void
  submitError: string | null
  submitLoading: boolean
  onSubmit: () => void
  onBackToSearch: () => void
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

function FormSection({ title, children }: { title: string; children: ReactNode }) {
  return (
    <section className="border-t border-(--tgui--divider_color) pt-5 first:border-t-0 first:pt-0">
      {title !== '' ? <p className="text-sm font-medium text-(--tgui--text_color)">{title}</p> : null}
      {children}
    </section>
  )
}

export function RatedCardScrollForm(props: RatedCardScrollFormProps) {
  const navigate = useNavigate()
  const watchNoteRef = useRef<HTMLTextAreaElement>(null)

  const plannedParams = useMemo(() => plannedCardLookupParams(props.binding), [props.binding])
  const plannedQuery = useQuery({
    queryKey: ['myPlannedCard', plannedParams],
    queryFn: () => getMyPlannedCard(plannedParams!),
    enabled: plannedParams != null,
    retry: false,
  })

  const customTagsLower = useMemo(
    () => new Set(props.customTags.map((t) => t.toLowerCase())),
    [props.customTags],
  )

  const popularTagSuggestions = useMemo(() => {
    const out: MyMovieCardTagStatItem[] = []
    for (const row of props.myTagStats) {
      if (customTagsLower.has(row.tag.toLowerCase())) continue
      out.push(row)
      if (out.length >= 14) break
    }
    return out
  }, [props.myTagStats, customTagsLower])

  const inputPrefixSuggestions = useMemo(() => {
    const raw = props.tagInput.trim()
    if (raw === '') return []
    const p = raw.toLowerCase()
    const out: MyMovieCardTagStatItem[] = []
    for (const row of props.myTagStats) {
      if (customTagsLower.has(row.tag.toLowerCase())) continue
      if (!row.tag.toLowerCase().startsWith(p)) continue
      out.push(row)
      if (out.length >= 24) break
    }
    return out
  }, [props.tagInput, props.myTagStats, customTagsLower])

  const tagInputTooLong = props.tagInput.trim().length > MAX_CUSTOM_TAG_LEN
  const watchNoteTooLong = props.watchNote.length > MAX_WATCH_NOTE_LEN
  const titleMissing = props.title.trim() === ''
  const canSubmit =
    !tagInputTooLong && !watchNoteTooLong && !titleMissing && !props.submitLoading

  const insertReactionIntoWatchNote = useCallback(
    (id: number) => {
      const token = reactionTokenFromId(id)
      const el = watchNoteRef.current
      const inserted = insertSnippetAtCaret(
        props.watchNote,
        el?.selectionStart ?? null,
        el?.selectionEnd ?? null,
        token,
        MAX_WATCH_NOTE_LEN,
      )
      if (!inserted) return
      props.onWatchNoteChange(inserted.nextValue)
      window.requestAnimationFrame(() => {
        const target = watchNoteRef.current
        if (!target) return
        target.focus()
        target.setSelectionRange(inserted.caret, inserted.caret)
      })
    },
    [props],
  )

  const toggleSpoilerInWatchNote = useCallback(() => {
    const el = watchNoteRef.current
    const toggled = toggleSpoilerAtSelection(
      props.watchNote,
      el?.selectionStart ?? null,
      el?.selectionEnd ?? null,
      MAX_WATCH_NOTE_LEN,
    )
    if (toggled == null) return
    props.onWatchNoteChange(toggled.nextValue)
    window.requestAnimationFrame(() => {
      const target = watchNoteRef.current
      if (!target) return
      target.focus()
      target.setSelectionRange(toggled.caret, toggled.caret)
    })
  }, [props])

  return (
    <div className="filmony-text-panel flex flex-col gap-5">
      {props.duplicateMyCardId != null && props.duplicateMyCardId > 0 ? (
        <div className="rounded-xl border border-(--tgui--divider_color) bg-(--tgui--secondary_bg_color) px-3 py-2.5">
          <p className="text-sm text-(--tgui--text_color)">У вас уже есть карточка на эту тему в профиле.</p>
          <div className="mt-2 flex flex-col gap-2">
            <Button stretched size="s" onClick={() => void navigate(`/cards/${props.duplicateMyCardId}`)}>
              Открыть мою карточку
            </Button>
            <Button
              mode="gray"
              stretched
              size="s"
              onClick={() => void navigate(`/cards/${props.duplicateMyCardId}/edit`)}
            >
              Редактировать карточку
            </Button>
          </div>
        </div>
      ) : null}

      {plannedQuery.isSuccess ? (
        <div className="rounded-xl border border-(--tgui--divider_color) bg-[color-mix(in_srgb,var(--tgui--link_color)_8%,var(--tgui--bg_color))] px-3 py-2.5">
          <p className="text-sm text-(--tgui--text_color)">
            Эта тема уже в списке «Позже» — при сохранении карточки заметка и полка могут перенестись из планируемой
            записи.
          </p>
        </div>
      ) : null}

      {props.remixFromCard && props.duplicateMyCardId == null ? (
        <p className="text-xs text-(--tgui--hint_color)">
          По мотивам чужой карточки — у вас будет отдельная запись со своей оценкой.
        </p>
      ) : null}

      <FormSection title="Название">
        <input
          type="text"
          autoComplete="off"
          value={props.title}
          onChange={(e) => props.onTitleChange(e.currentTarget.value)}
          className={`mt-2 ${CREATE_CARD_TEXT_FIELD_CLASS}`}
          placeholder="Название темы"
        />
        {titleMissing ? (
          <p className="mt-1 text-xs text-(--tgui--destructive_text_color)">Введите название</p>
        ) : null}
      </FormSection>

      <FormSection title="Коротко о чём">
        <textarea
          rows={3}
          value={props.summary}
          onChange={(e) => props.onSummaryChange(e.currentTarget.value)}
          placeholder="Одно-два предложения (необязательно)"
          className={`mt-2 min-h-20 resize-y ${CREATE_CARD_TEXT_FIELD_CLASS}`}
        />
      </FormSection>

      <FormSection title="Обложка">
        <div className="mt-3">
          <CardCoverBlock
            coverUrl={props.coverUrl}
            onCoverUrlChange={props.onCoverUrlChange}
            disabled={props.submitLoading}
          />
        </div>
      </FormSection>

      <FormSection title="">
        <div className="text-center">
          <p className="text-sm font-medium text-(--tgui--text_color)">Ваша оценка</p>
          <p className="mt-1 text-xs text-(--tgui--hint_color)">Шкала с шагом 0,5, максимум 10.</p>
          <p className="mt-2 text-4xl font-bold tabular-nums text-(--tgui--text_color)">
            {formatRating(props.rating)}
          </p>
          <div className="mt-3 flex justify-center gap-2">
            <Button
              mode="gray"
              size="s"
              type="button"
              onClick={() => props.onRatingChange(normalizeRating(props.rating - 0.5))}
            >
              −0.5
            </Button>
            <Button
              mode="gray"
              size="s"
              type="button"
              onClick={() => props.onRatingChange(normalizeRating(props.rating + 0.5))}
            >
              +0.5
            </Button>
          </div>
        </div>
      </FormSection>

      <FormSection title="С кем делились впечатлением">
        {renderChoiceChips(COMPANY_OPTIONS, props.company, props.onCompanyChange)}
      </FormSection>

      <FormSection title="Настроение до">
        {renderChoiceChips(MOOD_BEFORE_OPTIONS, props.moodBefore, props.onMoodBeforeChange)}
      </FormSection>

      <FormSection title="Настроение после">
        {renderChoiceChips(MOOD_AFTER_OPTIONS, props.moodAfter, props.onMoodAfterChange)}
      </FormSection>

      <FormSection title="Полка в коллекции">
        <p className="mt-1 text-xs text-(--tgui--hint_color)">
          Можно оставить автоматическую полку или выбрать свою.
        </p>
        {props.shelvesLoading ? (
          <p className="mt-2 text-xs text-(--tgui--hint_color)">Загрузка полок…</p>
        ) : props.shelvesError ? (
          <p className="mt-2 text-xs text-(--tgui--hint_color)">
            Полки временно недоступны — сервер подставит полку по умолчанию.
          </p>
        ) : (
          <>
            <label htmlFor="rated-card-shelf" className="sr-only">
              Полка коллекции
            </label>
            <select
              id="rated-card-shelf"
              className={`mt-3 ${CREATE_CARD_TEXT_FIELD_CLASS}`}
              value={props.selectedShelfId === null ? '' : String(props.selectedShelfId)}
              onChange={(e) => {
                const raw = e.currentTarget.value
                props.onSelectedShelfIdChange(raw === '' ? null : Number(raw))
              }}
            >
              <option value="">Авто (полка по умолчанию)</option>
              {props.shelves.map((row) => (
                <option key={row.id} value={String(row.id)}>
                  {row.name}
                </option>
              ))}
            </select>
            <div className="mt-2">
              <button
                type="button"
                className="text-sm font-medium text-(--tgui--link_color) active:opacity-80"
                onClick={() => props.onShelfCreateExpandedChange(!props.shelfCreateExpanded)}
              >
                {props.shelfCreateExpanded ? 'Скрыть создание полки' : '+ Новая полка'}
              </button>
              {props.shelfCreateExpanded ? (
                <div className="mt-2 rounded-xl border border-(--tgui--divider_color) bg-(--tgui--bg_color) p-3">
                  <div className="flex flex-col gap-2 sm:flex-row sm:items-stretch">
                    <input
                      type="text"
                      maxLength={120}
                      placeholder="Например: Триллеры 2025"
                      autoComplete="off"
                      value={props.newShelfDraft}
                      onChange={(e) => props.onNewShelfDraftChange(e.currentTarget.value)}
                      className={`min-w-0 flex-1 ${CREATE_CARD_TEXT_FIELD_CLASS}`}
                    />
                    <Button
                      mode="gray"
                      className="shrink-0 sm:self-stretch"
                      disabled={props.createShelfBusy}
                      type="button"
                      onClick={props.onCreateShelf}
                    >
                      {props.createShelfBusy ? '…' : 'Создать'}
                    </Button>
                  </div>
                  {props.shelfError != null ? (
                    <p className="mt-2 text-xs text-(--tgui--destructive_text_color)">{props.shelfError}</p>
                  ) : null}
                </div>
              ) : null}
            </div>
          </>
        )}
      </FormSection>

      <FormSection title="Свои теги (до 5)">
        <p className="mt-1 text-xs text-(--tgui--hint_color)">Короткие пометки об впечатлении — по желанию.</p>
        {popularTagSuggestions.length > 0 ? (
          <div className="mt-3">
            <p className="text-xs font-medium text-(--tgui--hint_color)">Часто у вас</p>
            <div className="mt-1.5 flex gap-1.5 overflow-x-auto pb-1 [-webkit-overflow-scrolling:touch]">
              {popularTagSuggestions.map((row) => (
                <button
                  key={row.tag}
                  type="button"
                  onClick={() => props.onAddTagFromSuggestion(row.tag)}
                  className="shrink-0 rounded-full border border-(--tgui--divider_color) bg-(--tgui--bg_color) px-3 py-1.5 text-xs text-(--tgui--text_color) active:opacity-90"
                >
                  {row.tag}
                  <span className="ml-1 tabular-nums text-(--tgui--hint_color)">{row.use_count}</span>
                </button>
              ))}
            </div>
          </div>
        ) : null}
        <div className="mt-3 flex flex-wrap items-stretch gap-2">
          <input
            type="text"
            placeholder="Добавить тег"
            value={props.tagInput}
            maxLength={MAX_CUSTOM_TAG_LEN + 8}
            onChange={(e) => props.onTagInputChange(e.currentTarget.value)}
            className={`min-w-0 flex-1 ${CREATE_CARD_TEXT_FIELD_CLASS}`}
          />
          <Button mode="gray" className="shrink-0 sm:self-stretch" disabled={tagInputTooLong} onClick={props.onAddTag}>
            Добавить
          </Button>
        </div>
        {props.tagFieldError != null ? (
          <p className="mt-1.5 text-xs text-(--tgui--destructive_text_color)">{props.tagFieldError}</p>
        ) : tagInputTooLong ? (
          <p className="mt-1.5 text-xs text-(--tgui--destructive_text_color)">
            Не больше {MAX_CUSTOM_TAG_LEN} символов в одном теге ({props.tagInput.trim().length}/{MAX_CUSTOM_TAG_LEN})
          </p>
        ) : (
          <p className="mt-1.5 text-xs text-(--tgui--hint_color)">До {MAX_CUSTOM_TAG_LEN} символов в теге.</p>
        )}
        {inputPrefixSuggestions.length > 0 ? (
          <div
            className="mt-2 max-h-40 overflow-y-auto rounded-xl border border-(--tgui--divider_color) bg-(--tgui--bg_color) py-1"
            role="listbox"
            aria-label="Подходящие теги"
          >
            {inputPrefixSuggestions.map((row) => (
              <button
                key={row.tag}
                type="button"
                role="option"
                className="flex w-full items-center justify-between gap-2 px-3 py-2 text-left text-sm text-(--tgui--text_color) hover:bg-(--tgui--secondary_bg_color)"
                onClick={() => props.onAddTagFromSuggestion(row.tag)}
              >
                <span className="min-w-0 truncate">{row.tag}</span>
                <span className="shrink-0 tabular-nums text-xs text-(--tgui--hint_color)">{row.use_count}</span>
              </button>
            ))}
          </div>
        ) : null}
        {props.customTags.length > 0 ? (
          <div className="mt-3 flex flex-wrap gap-2">
            {props.customTags.map((tag) => (
              <button
                key={tag}
                type="button"
                className="rounded-xl border border-(--tgui--divider_color) bg-(--tgui--secondary_bg_color) px-3 py-1 text-xs text-(--tgui--text_color)"
                onClick={() => props.onRemoveTag(tag)}
                title="Удалить тег"
              >
                {tag} ×
              </button>
            ))}
          </div>
        ) : (
          <p className="mt-3 text-sm text-(--tgui--hint_color)">Теги необязательны — можно оставить пустыми.</p>
        )}
      </FormSection>

      <FormSection title="Заметка к карточке">
        <p className="mt-1 text-xs text-(--tgui--hint_color)">
          По желанию — до {MAX_WATCH_NOTE_LEN} символов. Реакции можно вставить кнопкой справа.
        </p>
        <div className="mt-2 flex gap-2">
          <CommentDraftMultiline
            ref={watchNoteRef}
            value={props.watchNote}
            onChange={props.onWatchNoteChange}
            placeholder="Например: неожиданно тихий финал…"
            ariaLabel="Заметка к карточке"
            maxLength={MAX_WATCH_NOTE_LEN}
            rows={4}
            wrapperClassName={`min-h-24 flex-1 ${CREATE_CARD_TEXT_FIELD_CLASS}`}
          />
          <div className="flex shrink-0 flex-col justify-start gap-1 pt-1">
            <CommentReactionTokenPicker
              allowInsert={props.watchNote.length < MAX_WATCH_NOTE_LEN}
              onPickReactionTypeId={insertReactionIntoWatchNote}
            />
            <CommentSpoilerToggleButton
              allowInsert={props.watchNote.length < MAX_WATCH_NOTE_LEN}
              onToggleSpoiler={toggleSpoilerInWatchNote}
            />
          </div>
        </div>
        {watchNoteTooLong ? (
          <p className="mt-1 text-xs text-(--tgui--destructive_text_color)">
            Не больше {MAX_WATCH_NOTE_LEN} символов
          </p>
        ) : (
          <p className="mt-1 text-xs text-(--tgui--hint_color)">
            {props.watchNote.length}/{MAX_WATCH_NOTE_LEN}
          </p>
        )}
      </FormSection>

      {props.submitError != null ? (
        <p className="text-sm text-(--tgui--destructive_text_color)">{props.submitError}</p>
      ) : null}

      <div className="flex flex-col gap-2 border-t border-(--tgui--divider_color) pt-5">
        <Button stretched disabled={!canSubmit} onClick={props.onSubmit}>
          {props.submitLoading ? 'Сохраняем карточку…' : 'Сохранить карточку'}
        </Button>
        <Button mode="gray" stretched type="button" onClick={props.onBackToSearch}>
          Изменить тему
        </Button>
      </div>
    </div>
  )
}
