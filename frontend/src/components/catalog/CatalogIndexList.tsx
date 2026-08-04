import { Button, Section } from '@telegram-apps/telegram-ui'
import { Link } from 'react-router'

import { formatFilmsCount } from '../../lib/formatRuPlural'
import { ListErrorState } from '../ui/ListErrorState'
import { CatalogIndexSkeleton } from './CatalogIndexSkeleton'

export type CatalogIndexListItem = {
  key: string
  label: string
  href: string
  filmsCount: number
  linkClassName?: string
}

type CatalogIndexListProps = {
  items: CatalogIndexListItem[]
  isPending: boolean
  errorMessage: string | null
  onRetry?: () => void
  emptyMessage: string
  hasNextPage: boolean
  isFetchingNextPage: boolean
  onLoadMore: () => void
}

export function CatalogIndexList({
  items,
  isPending,
  errorMessage,
  onRetry,
  emptyMessage,
  hasNextPage,
  isFetchingNextPage,
  onLoadMore,
}: CatalogIndexListProps) {
  return (
    <>
      {isPending ? <CatalogIndexSkeleton /> : null}

      {errorMessage != null ? (
        <div className="mt-4">
          <ListErrorState message={errorMessage} onRetry={onRetry} />
        </div>
      ) : null}

      {items.length === 0 && !isPending && errorMessage == null ? (
        <p className="mt-6 text-sm text-(--tgui--hint_color)">{emptyMessage}</p>
      ) : (
        <Section header="Список">
          <ul className="divide-y divide-(--tgui--divider_color)">
            {items.map((row) => (
              <li key={row.key}>
                <Link
                  to={row.href}
                  className={`flex items-center justify-between gap-3 px-3 py-3 no-underline outline-none transition-[background-color] active:bg-[color-mix(in_srgb,var(--tgui--secondary_bg_color)_88%,transparent)] focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-(--tgui--link_color) ${row.linkClassName ?? ''}`}
                >
                  <span className="min-w-0 truncate text-sm font-medium text-(--tgui--text_color)">
                    {row.label}
                  </span>
                  <span className="shrink-0 text-xs tabular-nums text-(--tgui--hint_color)">
                    {formatFilmsCount(row.filmsCount)}
                  </span>
                </Link>
              </li>
            ))}
          </ul>
        </Section>
      )}

      {hasNextPage ? (
        <div className="mt-4">
          <Button
            stretched
            mode="bezeled"
            disabled={isFetchingNextPage}
            onClick={() => {
              onLoadMore()
            }}
          >
            {isFetchingNextPage ? 'Подгружаем…' : 'Подгрузить ещё'}
          </Button>
        </div>
      ) : null}
    </>
  )
}
