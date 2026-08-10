import { useEffect, useMemo, useState } from 'react'
import { Link, useNavigate } from 'react-router'
import { useQuery } from '@tanstack/react-query'

import { listTasteQuizKnowledge } from '../api/tasteQuizApi'
import type { TasteQuizKnowledgeDirection, TasteQuizKnowledgeItem } from '../api/tasteQuizTypes'
import { useAuthStatus } from '../auth/useAuthStatus'
import { TasteQuizKnowledgeList } from '../components/tasteQuiz/TasteQuizKnowledgeList'
import { PageErrorState } from '../components/ui/PageErrorState'
import { PageLoadingState } from '../components/ui/PageLoadingState'
import { tasteQuizKnowledgeListQueryKey } from '../lib/tasteQuizQueryKeys'

const TABS: { id: TasteQuizKnowledgeDirection; label: string; empty: string }[] = [
  {
    id: 'to_them',
    label: 'Я → они',
    empty:
      'Вы ещё ни с кем не играли. Подпишитесь на друзей и нажмите «Угадать вкус» в их профиле.',
  },
  {
    id: 'to_me',
    label: 'Они → я',
    empty: 'Вас ещё никто не угадывал. Пригласите подписчиков — кнопка «Пригласить угадать».',
  },
]

export function TasteQuizStatsPage() {
  const auth = useAuthStatus()
  const navigate = useNavigate()
  const [tab, setTab] = useState<TasteQuizKnowledgeDirection>('to_them')
  const [extraItems, setExtraItems] = useState<TasteQuizKnowledgeItem[]>([])
  const [nextCursor, setNextCursor] = useState<string | null>(null)
  const [loadingMore, setLoadingMore] = useState(false)

  const listQuery = useQuery({
    queryKey: tasteQuizKnowledgeListQueryKey(tab, null),
    queryFn: () => listTasteQuizKnowledge(tab),
    enabled: auth.kind === 'ready',
  })

  useEffect(() => {
    queueMicrotask(() => {
      setExtraItems([])
      setNextCursor(null)
    })
  }, [tab])

  const activeTab = TABS.find((t) => t.id === tab) ?? TABS[0]
  const displayItems = useMemo(
    () => [...(listQuery.data?.items ?? []), ...extraItems],
    [listQuery.data?.items, extraItems],
  )
  const hasMore = (nextCursor ?? listQuery.data?.next_cursor ?? null) != null

  async function loadMore() {
    const cursor = nextCursor ?? listQuery.data?.next_cursor ?? null
    if (cursor == null || loadingMore) return
    setLoadingMore(true)
    try {
      const page = await listTasteQuizKnowledge(tab, cursor)
      setExtraItems((prev) => [...prev, ...page.items])
      setNextCursor(page.next_cursor)
    } finally {
      setLoadingMore(false)
    }
  }

  if (auth.kind === 'loading' || auth.kind === 'unauthenticated') {
    return <PageLoadingState authPending className="bg-(--tgui--bg_color)" />
  }

  if (auth.kind === 'error') {
    return (
      <PageErrorState message={auth.message} backLabel="На главную" backHref="/" className="bg-(--tgui--bg_color)" />
    )
  }

  return (
    <div className="min-h-dvh bg-(--tgui--bg_color) text-(--tgui--text_color)">
      <header className="sticky top-0 z-20 flex items-center gap-2 border-b border-(--tgui--divider_color) bg-[color-mix(in_srgb,var(--tgui--bg_color)_88%,transparent)] px-2 py-2 backdrop-blur-md">
        <button
          type="button"
          className="flex min-h-10 min-w-10 items-center justify-center rounded-xl text-lg text-(--tgui--link_color)"
          aria-label="Назад"
          onClick={() => void navigate(-1)}
        >
          ←
        </button>
        <h1 className="min-w-0 flex-1 truncate text-base font-semibold tracking-tight">Угадай вкус</h1>
      </header>

      <main className="mx-auto max-w-md px-4 py-4">
        <div className="mb-4 grid grid-cols-2 gap-1 rounded-full bg-(--tgui--secondary_bg_color) p-1">
          {TABS.map((t) => (
            <button
              key={t.id}
              type="button"
              className={`rounded-full py-2.5 text-sm font-medium transition-all ${
                tab === t.id
                  ? 'bg-(--tgui--bg_color) text-(--tgui--text_color) shadow-sm'
                  : 'text-(--tgui--hint_color)'
              }`}
              onClick={() => setTab(t.id)}
            >
              {t.label}
            </button>
          ))}
        </div>

        {listQuery.isError ? (
          <PageErrorState
            message="Не удалось загрузить статистику"
            onRetry={() => void listQuery.refetch()}
          />
        ) : (
          <TasteQuizKnowledgeList
            items={displayItems}
            emptyCopy={activeTab.empty}
            loading={listQuery.isLoading}
            loadingMore={loadingMore}
            hasMore={hasMore}
            onLoadMore={() => void loadMore()}
          />
        )}

        {tab === 'to_me' && !listQuery.isLoading && displayItems.length > 0 ? (
          <Link
            to="/taste-quiz/invite"
            className="mt-6 block text-center text-sm text-(--tgui--link_color) no-underline"
          >
            Пригласить угадать
          </Link>
        ) : null}
      </main>
    </div>
  )
}
