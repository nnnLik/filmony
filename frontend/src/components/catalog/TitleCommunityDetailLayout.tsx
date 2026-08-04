import { Section, Title } from '@telegram-apps/telegram-ui'
import type { ReactNode } from 'react'

import { CatalogPageShell } from '../layout/CatalogPageShell'
import { DetailPageSkeleton } from '../ui/DetailPageSkeleton'
import { PageErrorState } from '../ui/PageErrorState'
import { resolveApiMediaUrl } from '../../lib/resolveApiMediaUrl'

export type TitleCommunityHeroVariant = 'film' | 'catalog'

export type TitleCommunityDetailLayoutProps = {
  headerLabel: string
  loading: boolean
  error: string | null
  sectionHeader?: string
  heroVariant: TitleCommunityHeroVariant
  title: string
  posterUrl?: string | null
  posterAlt?: string
  titleMeta?: ReactNode
  shortDescription?: string | null
  longDescription?: string | null
  descExpanded: boolean
  onToggleDescription: () => void
  overlapPlacement?: 'above-section' | 'below-description'
  overlapBanner?: ReactNode
  watchlistActions?: ReactNode
  followingRatings?: ReactNode
  communityRatings: ReactNode
  ready?: boolean
}

function posterSrc(url: string | null | undefined, resolveMedia: boolean): string | undefined {
  const trimmed = url?.trim()
  if (trimmed == null || trimmed === '') return undefined
  if (!resolveMedia) return trimmed
  return resolveApiMediaUrl(trimmed) ?? trimmed
}

function DescriptionBlock({
  shortDescription,
  longDescription,
  descExpanded,
  onToggleDescription,
  expandThreshold,
  expandLabel,
  collapseLabel,
}: {
  shortDescription?: string | null
  longDescription?: string | null
  descExpanded: boolean
  onToggleDescription: () => void
  expandThreshold: number
  expandLabel: string
  collapseLabel: string
}) {
  const shortText = shortDescription?.trim() ?? ''
  const longText = longDescription?.trim() ?? ''
  if (shortText === '' && longText === '') return null

  return (
    <div className="mt-4 border-t border-(--tgui--divider_color) pt-4">
      {shortText !== '' ? (
        <p className="text-[14px] leading-relaxed text-(--tgui--text_color)">{shortText}</p>
      ) : null}
      {longText !== '' ? (
        <div className={shortText !== '' ? 'mt-3' : ''}>
          <p
            className={`text-[14px] leading-relaxed text-(--tgui--text_color) ${
              !descExpanded ? 'line-clamp-6' : ''
            }`}
          >
            {longText}
          </p>
          {longText.length > expandThreshold ? (
            <button
              type="button"
              className="mt-2 text-sm font-medium text-(--tgui--link_color)"
              onClick={onToggleDescription}
            >
              {descExpanded ? collapseLabel : expandLabel}
            </button>
          ) : null}
        </div>
      ) : null}
    </div>
  )
}

function FilmHero({
  title,
  posterUrl,
  posterAlt,
  titleMeta,
  shortDescription,
  longDescription,
  descExpanded,
  onToggleDescription,
  overlapBanner,
  watchlistActions,
}: Pick<
  TitleCommunityDetailLayoutProps,
  | 'title'
  | 'posterUrl'
  | 'posterAlt'
  | 'titleMeta'
  | 'shortDescription'
  | 'longDescription'
  | 'descExpanded'
  | 'onToggleDescription'
  | 'overlapBanner'
  | 'watchlistActions'
>) {
  const src = posterSrc(posterUrl, false)

  return (
    <div className="px-3 py-3">
      <div className="filmony-text-panel flex gap-3">
        <div className="h-40 w-28 shrink-0 overflow-hidden rounded-xl bg-(--tgui--secondary_bg_color)">
          {src != null ? (
            <img src={src} alt={posterAlt ?? title} className="h-full w-full object-cover" />
          ) : null}
        </div>
        <div className="min-w-0">
          <Title level="3" weight="2">
            {title}
          </Title>
          {titleMeta}
        </div>
      </div>

      <DescriptionBlock
        shortDescription={shortDescription}
        longDescription={longDescription}
        descExpanded={descExpanded}
        onToggleDescription={onToggleDescription}
        expandThreshold={320}
        expandLabel="Полное описание"
        collapseLabel="Свернуть описание"
      />

      {overlapBanner != null || watchlistActions != null ? (
        <div className="mt-6 flex flex-col gap-2">
          {overlapBanner}
          {watchlistActions}
        </div>
      ) : null}
    </div>
  )
}

function CatalogHero({
  title,
  posterUrl,
  shortDescription,
  longDescription,
  descExpanded,
  onToggleDescription,
  watchlistActions,
}: Pick<
  TitleCommunityDetailLayoutProps,
  | 'title'
  | 'posterUrl'
  | 'shortDescription'
  | 'longDescription'
  | 'descExpanded'
  | 'onToggleDescription'
  | 'watchlistActions'
>) {
  const src = posterSrc(posterUrl, true)
  const longText = longDescription?.trim() ?? ''

  return (
    <div className="flex flex-col gap-4 px-3 py-3">
      {src != null ? (
        <img src={src} alt="" className="mx-auto max-h-72 w-auto max-w-full rounded-xl object-cover" />
      ) : null}
      <div>
        <Title level="2" weight="2">
          {title}
        </Title>
        {shortDescription?.trim() ? (
          <p className="mt-2 text-[14px] leading-relaxed text-(--tgui--hint_color)">
            {shortDescription.trim()}
          </p>
        ) : null}
        {longText !== '' ? (
          <div className="mt-2">
            <p
              className={
                descExpanded
                  ? 'text-[14px] leading-relaxed text-(--tgui--text_color)'
                  : 'line-clamp-4 text-[14px] leading-relaxed text-(--tgui--text_color)'
              }
            >
              {longText}
            </p>
            {longText.length > 200 ? (
              <button
                type="button"
                className="mt-1 text-xs font-medium text-(--tgui--link_color)"
                onClick={onToggleDescription}
              >
                {descExpanded ? 'Свернуть' : 'Показать полностью'}
              </button>
            ) : null}
          </div>
        ) : null}
      </div>

      {watchlistActions != null ? <div className="flex flex-col gap-2">{watchlistActions}</div> : null}
    </div>
  )
}

export function TitleCommunityDetailLayout({
  headerLabel,
  loading,
  error,
  sectionHeader,
  heroVariant,
  title,
  posterUrl,
  posterAlt,
  titleMeta,
  shortDescription,
  longDescription,
  descExpanded,
  onToggleDescription,
  overlapPlacement = 'below-description',
  overlapBanner,
  watchlistActions,
  followingRatings,
  communityRatings,
  ready = true,
}: TitleCommunityDetailLayoutProps) {
  const showContent = !loading && error == null && ready

  return (
    <CatalogPageShell headerTitle={headerLabel} mainClassName="mx-auto max-w-md space-y-4 px-4 pt-4">
      {loading ? <DetailPageSkeleton /> : null}
      {!loading && error != null ? (
        <PageErrorState message={error} backHref="/" backLabel="На главную" className="min-h-0 py-6" />
      ) : null}
      {showContent ? (
        <>
          {overlapPlacement === 'above-section' && overlapBanner != null ? overlapBanner : null}

          <Section header={sectionHeader}>
            {heroVariant === 'film' ? (
              <FilmHero
                title={title}
                posterUrl={posterUrl}
                posterAlt={posterAlt}
                titleMeta={titleMeta}
                shortDescription={shortDescription}
                longDescription={longDescription}
                descExpanded={descExpanded}
                onToggleDescription={onToggleDescription}
                overlapBanner={overlapPlacement === 'below-description' ? overlapBanner : undefined}
                watchlistActions={watchlistActions}
              />
            ) : (
              <CatalogHero
                title={title}
                posterUrl={posterUrl}
                shortDescription={shortDescription}
                longDescription={longDescription}
                descExpanded={descExpanded}
                onToggleDescription={onToggleDescription}
                watchlistActions={watchlistActions}
              />
            )}
          </Section>

          {followingRatings}
          <Section header="Оценки в Filmony">{communityRatings}</Section>
        </>
      ) : null}
    </CatalogPageShell>
  )
}
