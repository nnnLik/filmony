import { Button } from '@telegram-apps/telegram-ui'
import { Sparkles } from 'lucide-react'
import { useMemo, useState } from 'react'
import { useNavigate, useParams } from 'react-router'
import { useQuery } from '@tanstack/react-query'

import { ApiError, formatApiDetail } from '../api/client'
import { resolveTasteQuizInvite } from '../api/tasteQuizApi'
import { subscribeToUser } from '../api/profileApi'
import { useAuthStatus } from '../auth/useAuthStatus'
import { TasteQuizGateScreen } from '../components/tasteQuiz/TasteQuizGateScreen'
import { TasteQuizFollowSoftBanner } from '../components/tasteQuiz/TasteQuizFollowSoftBanner'
import { PageErrorState } from '../components/ui/PageErrorState'
import { PageLoadingState } from '../components/ui/PageLoadingState'
import { TabEmptyState } from '../components/ui/TabEmptyState'
import { displayNameFromProfile } from '../lib/profileDisplay'
import { tasteQuizResolveInviteQueryKey } from '../lib/tasteQuizQueryKeys'

export function TasteQuizInviteLandingPage() {
  const auth = useAuthStatus()
  const navigate = useNavigate()
  const { inviteToken: tokenParam } = useParams<{ inviteToken?: string }>()
  const token = useMemo(() => decodeURIComponent(tokenParam ?? '').trim(), [tokenParam])

  const [followBusy, setFollowBusy] = useState(false)
  const [following, setFollowing] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const inviteQuery = useQuery({
    queryKey: tasteQuizResolveInviteQueryKey(token),
    queryFn: () => resolveTasteQuizInvite(token),
    enabled: auth.kind === 'ready' && token !== '',
  })

  const owner = inviteQuery.data?.owner ?? null
  const ownerName =
    owner != null
      ? displayNameFromProfile({
          username: owner.profile_slug,
          first_name: null,
          last_name: null,
          display_name: owner.display_name,
        })
      : 'пользователя'

  function startQuiz() {
    if (owner == null || token === '') return
    void navigate(
      `/taste-quiz/play/${encodeURIComponent(owner.user_id)}?invite=${encodeURIComponent(token)}`,
    )
  }

  async function followOwner() {
    if (owner == null) return
    setFollowBusy(true)
    try {
      await subscribeToUser(owner.user_id)
      setFollowing(true)
    } catch (e: unknown) {
      setError(e instanceof ApiError ? formatApiDetail(e.detail) : 'Не удалось подписаться')
    } finally {
      setFollowBusy(false)
    }
  }

  if (auth.kind === 'loading') {
    return <PageLoadingState authPending className="bg-(--tgui--bg_color)" />
  }

  if (auth.kind === 'error') {
    return (
      <PageErrorState message={auth.message} backLabel="На главную" backHref="/" className="bg-(--tgui--bg_color)" />
    )
  }

  if (token === '') {
    return (
      <PageErrorState
        message="Некорректная ссылка"
        backLabel="На главную"
        backHref="/"
        className="bg-(--tgui--bg_color)"
      />
    )
  }

  if (inviteQuery.isLoading) {
    return <PageLoadingState message="Загрузка…" className="bg-(--tgui--bg_color)" />
  }

  if (inviteQuery.isError) {
    return (
      <PageErrorState
        message={
          inviteQuery.error instanceof ApiError
            ? formatApiDetail(inviteQuery.error.detail)
            : 'Приглашение не найдено'
        }
        backLabel="На главную"
        backHref="/"
        className="bg-(--tgui--bg_color)"
      />
    )
  }

  const data = inviteQuery.data

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
        <Sparkles className="size-5 shrink-0 text-(--tgui--link_color)" aria-hidden />
        <h1 className="min-w-0 flex-1 truncate text-base font-semibold tracking-tight">
          Приглашение в квиз
        </h1>
      </header>

      <main className="mx-auto max-w-md px-4 py-6">
        {data != null && data.reason === 'owner_insufficient_cards' ? (
          <TasteQuizGateScreen
            ownerName={ownerName}
            ownerRatedCount={data.owner_rated_count}
            gateMinRatedCards={data.gate_min_rated_cards}
            onBack={() => void navigate(-1)}
          />
        ) : null}

        {data != null && data.reason !== 'owner_insufficient_cards' && !data.expired ? (
          <div className="space-y-4">
            <div className="rounded-2xl border border-(--tgui--divider_color) bg-(--tgui--secondary_bg_color) px-4 py-6 text-center">
              <p className="text-lg font-semibold text-(--tgui--text_color)">{ownerName}</p>
              <p className="filmony-text-panel mt-2 text-sm leading-relaxed text-(--tgui--hint_color)">
                приглашает угадать его вкус в Filmony — до 10 карточек за раунд.
              </p>
            </div>

            {owner != null ? (
              <TasteQuizFollowSoftBanner
                ownerName={ownerName}
                ownerUserId={owner.user_id}
                following={following}
                followBusy={followBusy}
                onFollow={() => void followOwner()}
              />
            ) : null}

            {error != null ? (
              <p className="filmony-text-panel text-center text-sm text-(--tgui--destructive_text_color)">
                {error}
              </p>
            ) : null}

            <Button stretched disabled={!data.can_play} onClick={() => void startQuiz()}>
              Угадать вкус
            </Button>
          </div>
        ) : null}

        {data?.expired === true ? (
          <TabEmptyState fallback="Приглашение больше не действует." className="py-8" />
        ) : null}
      </main>
    </div>
  )
}
