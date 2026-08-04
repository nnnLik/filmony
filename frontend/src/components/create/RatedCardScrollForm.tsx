import { Button } from '@telegram-apps/telegram-ui'
import { useQuery } from '@tanstack/react-query'
import { useMemo, type ReactNode } from 'react'
import { useNavigate } from 'react-router'

import type { CardCompany, CardMoodAfter, CardMoodBefore, MyMovieCardTagStatItem } from '../../api/profileTypes'
import { getMyPlannedCard } from '../../api/profileApi'
import { CardCoverBlock } from './CardCoverBlock'
import { CardFormFields } from './CardFormFields'
import {
  CREATE_CARD_TEXT_FIELD_CLASS,
  MAX_CUSTOM_TAG_LEN,
  plannedCardLookupParams,
  type CreationBinding,
} from '../../lib/createCardBinding'

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
  viewerUserId?: string | number | null
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

  const plannedParams = useMemo(() => plannedCardLookupParams(props.binding), [props.binding])
  const plannedQuery = useQuery({
    queryKey: ['myPlannedCard', plannedParams],
    queryFn: () => getMyPlannedCard(plannedParams!),
    enabled: plannedParams != null,
    retry: false,
  })

  const tagInputTooLong = props.tagInput.trim().length > MAX_CUSTOM_TAG_LEN
  const titleMissing = props.title.trim() === ''
  const canSubmit =
    !tagInputTooLong && !titleMissing && !props.submitLoading

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

      <CardFormFields
        variant="create"
        rating={props.rating}
        onRatingChange={props.onRatingChange}
        company={props.company}
        onCompanyChange={props.onCompanyChange}
        moodBefore={props.moodBefore}
        onMoodBeforeChange={props.onMoodBeforeChange}
        moodAfter={props.moodAfter}
        onMoodAfterChange={props.onMoodAfterChange}
        viewerUserId={props.viewerUserId}
        watchNote={props.watchNote}
        onWatchNoteChange={props.onWatchNoteChange}
        shelf={{
          mode: 'create',
          selectedShelfId: props.selectedShelfId,
          onSelectedShelfIdChange: props.onSelectedShelfIdChange,
          shelves: props.shelves,
          shelvesLoading: props.shelvesLoading,
          shelvesError: props.shelvesError,
          shelfCreateExpanded: props.shelfCreateExpanded,
          onShelfCreateExpandedChange: props.onShelfCreateExpandedChange,
          newShelfDraft: props.newShelfDraft,
          onNewShelfDraftChange: props.onNewShelfDraftChange,
          shelfError: props.shelfError,
          createShelfBusy: props.createShelfBusy,
          onCreateShelf: props.onCreateShelf,
        }}
        tags={{
          mode: 'create',
          customTags: props.customTags,
          tagInput: props.tagInput,
          onTagInputChange: props.onTagInputChange,
          tagFieldError: props.tagFieldError,
          onAddTag: props.onAddTag,
          onAddTagFromSuggestion: props.onAddTagFromSuggestion,
          onRemoveTag: props.onRemoveTag,
          myTagStats: props.myTagStats,
        }}
      />

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
