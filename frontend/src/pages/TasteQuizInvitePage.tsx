import { Button } from '@telegram-apps/telegram-ui'
import { Sparkles } from 'lucide-react'
import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'

import { ApiError, formatApiDetail } from '../api/client'
import { createTasteQuizInvite } from '../api/tasteQuizApi'
import { getMyProfile, getUserSubscriptions } from '../api/profileApi'
import type { SubscriptionListItem } from '../api/profileTypes'
import { ShareFollowersPicker } from '../components/share/ShareFollowersPicker'
import { useAuthStatus } from '../auth/useAuthStatus'
import { buildMiniAppTasteQuizDeepLink } from '../lib/miniAppCardDeepLink'
import { copyTextToClipboard } from '../lib/copyTextToClipboard'
import { displayNameFromProfile } from '../lib/profileDisplay'
import { safeHapticSuccess } from '../lib/safeHaptic'
import { openTelegramShareUrl } from '../lib/telegramShare'

export function TasteQuizInvitePage() {
  const auth = useAuthStatus()
  const navigate = useNavigate()

  const [followers, setFollowers] = useState<SubscriptionListItem[]>([])
  const [selected, setSelected] = useState<Set<string>>(() => new Set())
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [inviteToken, setInviteToken] = useState<string | null>(null)
  const [shareText, setShareText] = useState<string | null>(null)
  const [ownerName, setOwnerName] = useState('')

  useEffect(() => {
    if (auth.kind !== 'ready') return
    let alive = true
    void (async () => {
      setLoading(true)
      setError(null)
      try {
        const me = await getMyProfile()
        if (!alive) return
        setOwnerName(displayNameFromProfile(me))
        const subs = await getUserSubscriptions(me.id, 'followers')
        if (!alive) return
        setFollowers(subs.items.filter((x) => x.relation_type === 'follower'))
        const invite = await createTasteQuizInvite()
        if (!alive) return
        setInviteToken(invite.invite_token)
        setShareText(invite.telegram_share_text)
      } catch (e: unknown) {
        if (!alive) return
        setError(e instanceof ApiError ? formatApiDetail(e.detail) : 'Не удалось создать приглашение')
      } finally {
        if (alive) setLoading(false)
      }
    })()
    return () => {
      alive = false
    }
  }, [auth.kind])

  function toggle(id: string) {
    setSelected((prev) => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  }

  async function copyShareLink() {
    const link = inviteToken != null ? buildMiniAppTasteQuizDeepLink(inviteToken) : null
    if (link == null) return
    const ok = await copyTextToClipboard(link)
    if (ok) safeHapticSuccess()
  }

  function shareTelegram() {
    const link = inviteToken != null ? buildMiniAppTasteQuizDeepLink(inviteToken) : null
    if (link == null) return
    const text = shareText ?? `${ownerName} приглашает угадать его вкус в Filmony`
    openTelegramShareUrl(link, text)
  }

  if (auth.kind === 'loading' || auth.kind === 'error' || auth.kind === 'skipped') {
    return (
      <div className="px-4 py-16 text-center text-sm text-(--tgui--hint_color)">
        <p className="filmony-text-panel inline-block">Загрузка…</p>
      </div>
    )
  }

  const deepLink = inviteToken != null ? buildMiniAppTasteQuizDeepLink(inviteToken) : null

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
          Пригласить угадать
        </h1>
      </header>

      <main className="mx-auto max-w-md px-4 py-4">
        {loading ? (
          <p className="filmony-text-panel py-10 text-center text-sm text-(--tgui--hint_color)">Загрузка…</p>
        ) : null}

        {!loading && error != null ? (
          <div className="py-8 text-center">
            <p className="filmony-text-panel text-sm text-(--tgui--destructive_text_color)">{error}</p>
            <Link className="mt-4 inline-block text-sm text-(--tgui--link_color)" to="/profile">
              В профиль
            </Link>
          </div>
        ) : null}

        {!loading && error == null ? (
          <div className="space-y-4">
            <ShareFollowersPicker
              preview={{
                posterUrl: null,
                title: 'Угадай мой вкус',
                yearLabel: 'Taste Quiz',
              }}
              hint="Выберите подписчиков и отправьте им ссылку на квиз в Telegram. Можно скопировать deep link и поделиться вручную."
              followers={followers}
              loading={false}
              selected={selected}
              onToggle={toggle}
              deepLinkToCopy={deepLink}
            />

            <Button mode="gray" stretched type="button" onClick={() => void copyShareLink()}>
              Скопировать ссылку
            </Button>

            <Button stretched type="button" onClick={shareTelegram}>
              Отправить в Telegram
            </Button>

            {selected.size > 0 ? (
              <p className="filmony-text-panel text-center text-xs text-(--tgui--hint_color)">
                Выбрано подписчиков: {selected.size}. Отправьте им ссылку через Telegram.
              </p>
            ) : null}
          </div>
        ) : null}
      </main>
    </div>
  )
}
