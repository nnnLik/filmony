import type { CatalogCandidate, CatalogCandidatesMeta } from '../../api/catalogApi'
import type { UserCardProvider } from '../../api/profileTypes'

type CatalogCandidatesListProps = {
  items: CatalogCandidate[]
  meta?: CatalogCandidatesMeta | null
  loading?: boolean
  errorMessage?: string | null
  pickBusy?: boolean
  onPick: (candidate: CatalogCandidate) => void
}

const PROVIDER_LABELS: Record<UserCardProvider, string> = {
  kinopoisk: 'Кинопоиск',
  rawg: 'RAWG',
  youtube: 'YouTube',
  no_provider: 'Без каталога',
}

const KIND_HINT_LABELS = {
  film: 'фильм',
  game: 'игра',
  video: 'видео',
} as const

function providerLabel(provider: UserCardProvider): string {
  return PROVIDER_LABELS[provider] ?? provider
}

function degradedSourcesHint(meta: CatalogCandidatesMeta | null | undefined): string | null {
  const sources = meta?.degraded_sources ?? []
  if (sources.length === 0) return null
  const labels = sources.map((s) => {
    if (s === 'kinopoisk') return 'Кинопоиск'
    if (s === 'rawg') return 'RAWG'
    return s
  })
  return `Часть каталогов временно недоступна: ${labels.join(', ')}.`
}

export function CatalogCandidatesList({
  items,
  meta,
  loading = false,
  errorMessage,
  pickBusy = false,
  onPick,
}: CatalogCandidatesListProps) {
  const degradedHint = degradedSourcesHint(meta)

  return (
    <div className="flex flex-col gap-2">
      {degradedHint != null ? (
        <p className="rounded-xl border border-(--tgui--divider_color) bg-(--tgui--secondary_bg_color) px-3 py-2 text-xs text-(--tgui--hint_color)">
          {degradedHint}
        </p>
      ) : null}

      {loading ? <p className="text-sm text-(--tgui--hint_color)">Ищем…</p> : null}

      {errorMessage != null ? (
        <p className="text-sm text-(--tgui--destructive_text_color)">{errorMessage}</p>
      ) : null}

      {items.length > 0 ? (
        <ul className="flex max-h-80 flex-col gap-2 overflow-y-auto [-webkit-overflow-scrolling:touch]">
          {items.map((candidate) => {
            const selectable = candidate.catalog_item_id != null && !pickBusy
            const kindHint = candidate.kind_hint ?? candidate.kind
            return (
              <li key={candidate.candidate_id}>
                <button
                  type="button"
                  disabled={!selectable}
                  onClick={() => {
                    if (!selectable) return
                    onPick(candidate)
                  }}
                  className="flex w-full gap-3 rounded-xl border border-(--tgui--divider_color) bg-(--tgui--bg_color) p-3 text-left transition active:scale-[0.99] disabled:cursor-not-allowed disabled:opacity-50"
                >
                  <div className="aspect-2/3 h-16 w-[2.625rem] shrink-0 overflow-hidden rounded-md bg-(--tgui--secondary_bg_color)">
                    {candidate.cover_url ? (
                      <img src={candidate.cover_url} alt="" className="h-full w-full object-cover" />
                    ) : (
                      <div className="flex h-full items-center justify-center text-[10px] text-(--tgui--hint_color)">
                        —
                      </div>
                    )}
                  </div>
                  <div className="min-w-0 flex-1">
                    <p className="text-sm font-medium text-(--tgui--text_color)">{candidate.title}</p>
                    {candidate.subtitle ? (
                      <p className="mt-0.5 line-clamp-2 text-xs text-(--tgui--hint_color)">
                        {candidate.subtitle}
                      </p>
                    ) : null}
                    <div className="mt-1.5 flex flex-wrap items-center gap-1.5">
                      <span className="rounded-md bg-(--tgui--secondary_bg_color) px-1.5 py-0.5 text-[10px] font-medium uppercase tracking-wide text-(--tgui--hint_color)">
                        {providerLabel(candidate.provider)}
                      </span>
                      <span className="rounded-md border border-(--tgui--divider_color) px-1.5 py-0.5 text-[10px] text-(--tgui--hint_color)">
                        {KIND_HINT_LABELS[kindHint]}
                      </span>
                      {candidate.source === 'local' ? (
                        <span className="text-[10px] text-(--tgui--hint_color)">в каталоге</span>
                      ) : null}
                      {candidate.degraded === true ? (
                        <span className="text-[10px] text-(--tgui--hint_color)">ограничено</span>
                      ) : null}
                    </div>
                  </div>
                </button>
              </li>
            )
          })}
        </ul>
      ) : null}
    </div>
  )
}
