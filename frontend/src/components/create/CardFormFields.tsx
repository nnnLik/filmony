import { Button, Section } from '@telegram-apps/telegram-ui'
import { useCallback, useMemo, useRef, type ReactNode } from 'react'

import type {
  CardCompany,
  CardMoodAfter,
  CardMoodBefore,
  MyMovieCardTagStatItem,
  MyUserCardCategory,
} from '../../api/profileTypes'
import { CommentDraftMultiline } from '../comments/CommentDraftMirrorField'
import { CommentReactionTokenPicker } from '../comments/CommentReactionTokenPicker'
import { CommentSpoilerToggleButton } from '../comments/CommentSpoilerToggleButton'
import { InlineLoadingState } from '../ui/InlineLoadingState'
import { PepeExtremeRatingBubble } from '../ui/PepeExtremeRatingBubble'
import {
  COMPANY_OPTIONS,
  MOOD_AFTER_OPTIONS,
  MOOD_BEFORE_OPTIONS,
} from '../../lib/cardFormOptions'
import {
  CREATE_CARD_TEXT_FIELD_CLASS,
  MAX_CUSTOM_TAG_LEN,
  formatRating,
  normalizeRating,
} from '../../lib/createCardBinding'
import { insertSnippetAtCaret, reactionTokenFromId } from '../../lib/commentReactionTokens'
import { toggleSpoilerAtSelection } from '../../lib/spoilerTokens'
import { useMicroFunLine } from '../../lib/microFun'
import { usePepeExtremeRatingJudge } from '../../hooks/usePepeExtremeRatingJudge'
import { CardChoiceChips } from './CardChoiceChips'

type ShelfRow = { id: number; name: string }

export type CardFormShelfEditConfig = {
  mode: 'edit'
  shelfRows: MyUserCardCategory[]
  shelfSelectControlId: number | null
  onShelfChange: (id: number | null) => void
  shelfSelectBusy: boolean
  shelvesError: boolean
  currentShelfName?: string
  disabled?: boolean
}

export type CardFormShelfCreateConfig = {
  mode: 'create'
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
}

export type CardFormTagsEditConfig = {
  mode: 'edit'
  customTags: string[]
  tagInput: string
  onTagInputChange: (value: string) => void
  onAddTag: () => void
  onRemoveTag: (tag: string) => void
  disabled?: boolean
}

export type CardFormTagsCreateConfig = {
  mode: 'create'
  customTags: string[]
  tagInput: string
  onTagInputChange: (value: string) => void
  tagFieldError: string | null
  onAddTag: () => void
  onAddTagFromSuggestion: (label: string) => void
  onRemoveTag: (tag: string) => void
  myTagStats: MyMovieCardTagStatItem[]
}

export type CardFormFieldsProps = {
  variant: 'edit' | 'create'
  rating: number
  onRatingChange: (value: number) => void
  company: CardCompany
  onCompanyChange: (value: CardCompany) => void
  moodBefore: CardMoodBefore
  onMoodBeforeChange: (value: CardMoodBefore) => void
  moodAfter: CardMoodAfter
  onMoodAfterChange: (value: CardMoodAfter) => void
  shelf: CardFormShelfEditConfig | CardFormShelfCreateConfig
  tags: CardFormTagsEditConfig | CardFormTagsCreateConfig
  watchNote: string
  onWatchNoteChange: (value: string) => void
  viewerUserId?: string | number | null
  watchNoteDisabled?: boolean
}

function FormSection({ title, children }: { title: string; children: ReactNode }) {
  return (
    <section className="border-t border-(--tgui--divider_color) pt-5 first:border-t-0 first:pt-0">
      {title !== '' ? <p className="text-sm font-medium text-(--tgui--text_color)">{title}</p> : null}
      {children}
    </section>
  )
}

function CardRatingContent({
  variant,
  rating,
  onRatingChange,
  viewerUserId,
}: Pick<CardFormFieldsProps, 'variant' | 'rating' | 'onRatingChange' | 'viewerUserId'>) {
  const pepeJudge = usePepeExtremeRatingJudge(rating, viewerUserId ?? null)

  const body = (
    <div className={variant === 'edit' ? 'px-3 py-3 text-center' : 'text-center'}>
      {variant === 'edit' ? (
        <p className="text-sm text-(--tgui--hint_color)">Текущая оценка</p>
      ) : (
        <>
          <p className="text-sm font-medium text-(--tgui--text_color)">Ваша оценка</p>
          <p className="mt-1 text-xs text-(--tgui--hint_color)">Шкала с шагом 0,5, максимум 10.</p>
        </>
      )}
      <p
        className={`${variant === 'edit' ? 'mt-1' : 'mt-2'} text-4xl font-bold tabular-nums text-(--tgui--text_color)`}
      >
        {formatRating(rating)}
      </p>
      <div className="mt-3 flex justify-center gap-2">
        <Button mode="gray" size="s" type="button" onClick={() => onRatingChange(normalizeRating(rating - 0.5))}>
          {variant === 'edit' ? '-0.5' : '−0.5'}
        </Button>
        <Button mode="gray" size="s" type="button" onClick={() => onRatingChange(normalizeRating(rating + 0.5))}>
          +0.5
        </Button>
      </div>
      <PepeExtremeRatingBubble message={pepeJudge.message} onDismiss={pepeJudge.dismiss} />
    </div>
  )

  if (variant === 'edit') {
    return <Section header="Оценка">{body}</Section>
  }

  return <FormSection title="">{body}</FormSection>
}

function CardMoodContent({
  variant,
  company,
  onCompanyChange,
  moodBefore,
  onMoodBeforeChange,
  moodAfter,
  onMoodAfterChange,
}: Pick<
  CardFormFieldsProps,
  | 'variant'
  | 'company'
  | 'onCompanyChange'
  | 'moodBefore'
  | 'onMoodBeforeChange'
  | 'moodAfter'
  | 'onMoodAfterChange'
>) {
  if (variant === 'edit') {
    return (
      <Section header="Контекст карточки">
        <div className="px-3 py-3">
          <p className="text-sm font-medium text-(--tgui--text_color)">С кем смотрели:</p>
          <CardChoiceChips options={COMPANY_OPTIONS} selected={company} onSelect={onCompanyChange} />
          <p className="mt-4 text-sm font-medium text-(--tgui--text_color)">Настроение до:</p>
          <CardChoiceChips options={MOOD_BEFORE_OPTIONS} selected={moodBefore} onSelect={onMoodBeforeChange} />
          <p className="mt-4 text-sm font-medium text-(--tgui--text_color)">Настроение после:</p>
          <CardChoiceChips options={MOOD_AFTER_OPTIONS} selected={moodAfter} onSelect={onMoodAfterChange} />
        </div>
      </Section>
    )
  }

  return (
    <>
      <FormSection title="С кем делились впечатлением">
        <CardChoiceChips options={COMPANY_OPTIONS} selected={company} onSelect={onCompanyChange} />
      </FormSection>
      <FormSection title="Настроение до">
        <CardChoiceChips options={MOOD_BEFORE_OPTIONS} selected={moodBefore} onSelect={onMoodBeforeChange} />
      </FormSection>
      <FormSection title="Настроение после">
        <CardChoiceChips options={MOOD_AFTER_OPTIONS} selected={moodAfter} onSelect={onMoodAfterChange} />
      </FormSection>
    </>
  )
}

function CardShelfEditContent({ shelf }: { shelf: CardFormShelfEditConfig }) {
  return (
    <Section header="Полка">
      <div className="px-3 py-3">
        {shelf.shelvesError ? (
          <p className="text-xs text-(--tgui--hint_color)">
            Не удалось загрузить список полок — положение можно поменять позже. Текущая:{' '}
            <span className="font-medium text-(--tgui--text_color)">
              {shelf.currentShelfName?.trim() !== '' ? shelf.currentShelfName : '—'}
            </span>
          </p>
        ) : shelf.shelfSelectBusy ? (
          <InlineLoadingState message="Загрузка полок…" className="py-0" />
        ) : shelf.shelfRows.length === 0 ? (
          <p className="text-xs text-(--tgui--hint_color)">
            Полок пока нет — сохранится текущее размещение на сервере.
          </p>
        ) : (
          <>
            <p className="text-xs text-(--tgui--hint_color)">Куда отнести карточку в вашей коллекции.</p>
            <select
              className="mt-2 w-full rounded-xl border border-(--tgui--divider_color) bg-(--tgui--bg_color) px-3 py-2.5 text-sm text-(--tgui--text_color) outline-none focus-visible:border-(--tgui--link_color) focus-visible:ring-2 focus-visible:ring-[color-mix(in_srgb,var(--tgui--link_color)_32%,transparent)]"
              value={shelf.shelfSelectControlId == null ? '' : String(shelf.shelfSelectControlId)}
              onChange={(e) => {
                const v = Number(e.currentTarget.value)
                shelf.onShelfChange(Number.isInteger(v) && v >= 1 ? v : null)
              }}
              disabled={shelf.disabled}
              aria-label="Полка карточки"
            >
              {shelf.shelfRows.map((row) => (
                <option key={row.id} value={String(row.id)}>
                  {row.name}
                </option>
              ))}
            </select>
          </>
        )}
      </div>
    </Section>
  )
}

function CardShelfCreateContent({ shelf }: { shelf: CardFormShelfCreateConfig }) {
  return (
    <FormSection title="Полка в коллекции">
      <p className="mt-1 text-xs text-(--tgui--hint_color)">
        Можно оставить автоматическую полку или выбрать свою.
      </p>
      {shelf.shelvesLoading ? (
        <p className="mt-2 text-xs text-(--tgui--hint_color)">Загрузка полок…</p>
      ) : shelf.shelvesError ? (
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
            value={shelf.selectedShelfId === null ? '' : String(shelf.selectedShelfId)}
            onChange={(e) => {
              const raw = e.currentTarget.value
              shelf.onSelectedShelfIdChange(raw === '' ? null : Number(raw))
            }}
          >
            <option value="">Авто (полка по умолчанию)</option>
            {shelf.shelves.map((row) => (
              <option key={row.id} value={String(row.id)}>
                {row.name}
              </option>
            ))}
          </select>
          <div className="mt-2">
            <button
              type="button"
              className="text-sm font-medium text-(--tgui--link_color) active:opacity-80"
              onClick={() => shelf.onShelfCreateExpandedChange(!shelf.shelfCreateExpanded)}
            >
              {shelf.shelfCreateExpanded ? 'Скрыть создание полки' : '+ Новая полка'}
            </button>
            {shelf.shelfCreateExpanded ? (
              <div className="mt-2 rounded-xl border border-(--tgui--divider_color) bg-(--tgui--bg_color) p-3">
                <div className="flex flex-col gap-2 sm:flex-row sm:items-stretch">
                  <input
                    type="text"
                    maxLength={120}
                    placeholder="Например: Триллеры 2025"
                    autoComplete="off"
                    value={shelf.newShelfDraft}
                    onChange={(e) => shelf.onNewShelfDraftChange(e.currentTarget.value)}
                    className={`min-w-0 flex-1 ${CREATE_CARD_TEXT_FIELD_CLASS}`}
                  />
                  <Button
                    mode="gray"
                    className="shrink-0 sm:self-stretch"
                    disabled={shelf.createShelfBusy}
                    type="button"
                    onClick={shelf.onCreateShelf}
                  >
                    {shelf.createShelfBusy ? '…' : 'Создать'}
                  </Button>
                </div>
                {shelf.shelfError != null ? (
                  <p className="mt-2 text-xs text-(--tgui--destructive_text_color)">{shelf.shelfError}</p>
                ) : null}
              </div>
            ) : null}
          </div>
        </>
      )}
    </FormSection>
  )
}

function CardTagsEditContent({ tags }: { tags: CardFormTagsEditConfig }) {
  return (
    <Section header="Свои теги (до 5)">
      <div className="px-3 py-3">
        <div className="flex flex-wrap items-stretch gap-2">
          <input
            type="text"
            className="min-w-0 flex-1 rounded-xl border border-(--tgui--divider_color) bg-(--tgui--bg_color) px-3 py-2.5 text-sm text-(--tgui--text_color) outline-none placeholder:text-(--tgui--hint_color) focus-visible:border-(--tgui--link_color) focus-visible:ring-2 focus-visible:ring-[color-mix(in_srgb,var(--tgui--link_color)_32%,transparent)]"
            placeholder="Добавить тег"
            value={tags.tagInput}
            maxLength={MAX_CUSTOM_TAG_LEN + 8}
            disabled={tags.disabled}
            onChange={(e) => tags.onTagInputChange(e.currentTarget.value)}
          />
          <Button mode="gray" className="shrink-0" disabled={tags.disabled} onClick={tags.onAddTag}>
            Добавить
          </Button>
        </div>
        {tags.customTags.length > 0 ? (
          <div className="mt-3 flex flex-wrap gap-2">
            {tags.customTags.map((tag) => (
              <button
                key={tag}
                type="button"
                className="rounded-xl border border-(--tgui--divider_color) bg-(--tgui--secondary_bg_color) px-3 py-1 text-xs text-(--tgui--text_color)"
                onClick={() => tags.onRemoveTag(tag)}
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
  )
}

function CardTagsCreateContent({ tags }: { tags: CardFormTagsCreateConfig }) {
  const customTagsLower = useMemo(
    () => new Set(tags.customTags.map((t) => t.toLowerCase())),
    [tags.customTags],
  )

  const popularTagSuggestions = useMemo(() => {
    const out: MyMovieCardTagStatItem[] = []
    for (const row of tags.myTagStats) {
      if (customTagsLower.has(row.tag.toLowerCase())) continue
      out.push(row)
      if (out.length >= 14) break
    }
    return out
  }, [tags.myTagStats, customTagsLower])

  const inputPrefixSuggestions = useMemo(() => {
    const raw = tags.tagInput.trim()
    if (raw === '') return []
    const p = raw.toLowerCase()
    const out: MyMovieCardTagStatItem[] = []
    for (const row of tags.myTagStats) {
      if (customTagsLower.has(row.tag.toLowerCase())) continue
      if (!row.tag.toLowerCase().startsWith(p)) continue
      out.push(row)
      if (out.length >= 24) break
    }
    return out
  }, [tags.tagInput, tags.myTagStats, customTagsLower])

  const tagInputTooLong = tags.tagInput.trim().length > MAX_CUSTOM_TAG_LEN

  return (
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
                onClick={() => tags.onAddTagFromSuggestion(row.tag)}
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
          value={tags.tagInput}
          maxLength={MAX_CUSTOM_TAG_LEN + 8}
          onChange={(e) => tags.onTagInputChange(e.currentTarget.value)}
          className={`min-w-0 flex-1 ${CREATE_CARD_TEXT_FIELD_CLASS}`}
        />
        <Button mode="gray" className="shrink-0 sm:self-stretch" disabled={tagInputTooLong} onClick={tags.onAddTag}>
          Добавить
        </Button>
      </div>
      {tags.tagFieldError != null ? (
        <p className="mt-1.5 text-xs text-(--tgui--destructive_text_color)">{tags.tagFieldError}</p>
      ) : tagInputTooLong ? (
        <p className="mt-1.5 text-xs text-(--tgui--destructive_text_color)">
          Не больше {MAX_CUSTOM_TAG_LEN} символов в одном теге ({tags.tagInput.trim().length}/{MAX_CUSTOM_TAG_LEN})
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
              onClick={() => tags.onAddTagFromSuggestion(row.tag)}
            >
              <span className="min-w-0 truncate">{row.tag}</span>
              <span className="shrink-0 tabular-nums text-xs text-(--tgui--hint_color)">{row.use_count}</span>
            </button>
          ))}
        </div>
      ) : null}
      {tags.customTags.length > 0 ? (
        <div className="mt-3 flex flex-wrap gap-2">
          {tags.customTags.map((tag) => (
            <button
              key={tag}
              type="button"
              className="rounded-xl border border-(--tgui--divider_color) bg-(--tgui--secondary_bg_color) px-3 py-1 text-xs text-(--tgui--text_color)"
              onClick={() => tags.onRemoveTag(tag)}
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
  )
}

function CardWatchNoteContent({
  variant,
  watchNote,
  onWatchNoteChange,
  viewerUserId,
  watchNoteDisabled: disabled,
}: Pick<CardFormFieldsProps, 'variant' | 'watchNote' | 'onWatchNoteChange' | 'viewerUserId' | 'watchNoteDisabled'>) {
  const watchNoteRef = useRef<HTMLTextAreaElement>(null)
  const watchNotePlaceholder = useMicroFunLine(
    'watch_note_placeholder',
    'Например: неожиданно тихий финал…',
    viewerUserId ?? null,
  )

  const insertReactionIntoWatchNote = useCallback(
    (id: number) => {
      const token = reactionTokenFromId(id)
      const el = watchNoteRef.current
      const inserted = insertSnippetAtCaret(
        watchNote,
        el?.selectionStart ?? null,
        el?.selectionEnd ?? null,
        token,
      )
      if (!inserted) return
      onWatchNoteChange(inserted.nextValue)
      window.requestAnimationFrame(() => {
        const target = watchNoteRef.current
        if (!target) return
        target.focus()
        target.setSelectionRange(inserted.caret, inserted.caret)
      })
    },
    [watchNote, onWatchNoteChange],
  )

  const toggleSpoilerInWatchNote = useCallback(() => {
    const el = watchNoteRef.current
    const toggled = toggleSpoilerAtSelection(
      watchNote,
      el?.selectionStart ?? null,
      el?.selectionEnd ?? null,
    )
    if (toggled == null) return
    onWatchNoteChange(toggled.nextValue)
    window.requestAnimationFrame(() => {
      const target = watchNoteRef.current
      if (!target) return
      target.focus()
      target.setSelectionRange(toggled.caret, toggled.caret)
    })
  }, [watchNote, onWatchNoteChange])

  const noteBody = (
    <>
      <p className={`${variant === 'edit' ? '' : 'mt-1'} text-xs text-(--tgui--hint_color)`}>
        {variant === 'edit' ? 'По желанию.' : 'По желанию. Реакции можно вставить кнопкой справа.'}
      </p>
      <div className="mt-2 flex gap-2">
        <CommentDraftMultiline
          ref={watchNoteRef}
          value={watchNote}
          onChange={onWatchNoteChange}
          placeholder={variant === 'edit' ? 'Коротко о впечатлении…' : watchNotePlaceholder}
          ariaLabel="Заметка к карточке"
          disabled={disabled}
          rows={variant === 'edit' ? 5 : 4}
          wrapperClassName={
            variant === 'edit'
              ? 'min-h-28 flex-1 focus-within:border-(--tgui--link_color) focus-within:ring-2 focus-within:ring-[color-mix(in_srgb,var(--tgui--link_color)_32%,transparent)]'
              : `min-h-24 flex-1 ${CREATE_CARD_TEXT_FIELD_CLASS}`
          }
        />
        <div className="flex shrink-0 flex-col justify-start gap-1 pt-1">
          <CommentReactionTokenPicker disabled={disabled} onPickReactionTypeId={insertReactionIntoWatchNote} />
          <CommentSpoilerToggleButton disabled={disabled} onToggleSpoiler={toggleSpoilerInWatchNote} />
        </div>
      </div>
      <p className="mt-1 text-xs text-(--tgui--hint_color) tabular-nums">{watchNote.length}</p>
    </>
  )

  if (variant === 'edit') {
    return (
      <Section header="Заметка к карточке">
        <div className="px-3 py-3">{noteBody}</div>
      </Section>
    )
  }

  return <FormSection title="Заметка к карточке">{noteBody}</FormSection>
}

export function CardFormFields(props: CardFormFieldsProps) {
  return (
    <>
      <CardRatingContent
        variant={props.variant}
        rating={props.rating}
        onRatingChange={props.onRatingChange}
        viewerUserId={props.viewerUserId}
      />
      <CardMoodContent
        variant={props.variant}
        company={props.company}
        onCompanyChange={props.onCompanyChange}
        moodBefore={props.moodBefore}
        onMoodBeforeChange={props.onMoodBeforeChange}
        moodAfter={props.moodAfter}
        onMoodAfterChange={props.onMoodAfterChange}
      />
      {props.shelf.mode === 'edit' ? (
        <CardShelfEditContent shelf={props.shelf} />
      ) : (
        <CardShelfCreateContent shelf={props.shelf} />
      )}
      {props.tags.mode === 'edit' ? (
        <CardTagsEditContent tags={props.tags} />
      ) : (
        <CardTagsCreateContent tags={props.tags} />
      )}
      <CardWatchNoteContent
        variant={props.variant}
        watchNote={props.watchNote}
        onWatchNoteChange={props.onWatchNoteChange}
        viewerUserId={props.viewerUserId}
        watchNoteDisabled={props.watchNoteDisabled}
      />
    </>
  )
}
