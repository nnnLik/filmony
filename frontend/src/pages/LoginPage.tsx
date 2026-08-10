import { Section, Title } from '@telegram-apps/telegram-ui'
import { useState } from 'react'
import { Navigate, useSearchParams } from 'react-router'

import { authTelegramWidget, type TelegramWidgetAuthPayload } from '../api/profileApi'
import { useAuthActions } from '../auth/useAuthActions'
import { useAuthStatus } from '../auth/useAuthStatus'
import { TelegramLoginWidget } from '../components/auth/TelegramLoginWidget'
import { PageLoadingState } from '../components/ui/PageLoadingState'
import { sanitizeReturnTo } from '../lib/sanitizeReturnTo'
import { writeAccessToken, writeAuthSessionFlag } from '../lib/filmonySession'

function loginErrorMessage(status: number): string {
  if (status === 401) {
    return 'Не удалось войти. Данные Telegram недействительны или устарели.'
  }
  if (status >= 500) {
    return 'Сервер временно недоступен. Попробуйте позже.'
  }
  return `Ошибка входа (HTTP ${status})`
}

export function LoginPage() {
  const auth = useAuthStatus()
  const { completeLogin } = useAuthActions()
  const [searchParams] = useSearchParams()
  const returnTo = sanitizeReturnTo(searchParams.get('returnTo'))
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const botUsername = import.meta.env.VITE_TELEGRAM_BOT_USERNAME?.trim() ?? ''

  if (auth.kind === 'ready') {
    return <Navigate to={returnTo} replace />
  }

  if (auth.kind === 'loading') {
    return <PageLoadingState authPending className="bg-(--tgui--bg_color)" />
  }

  async function handleAuth(user: TelegramWidgetAuthPayload) {
    setError(null)
    setBusy(true)
    try {
      const res = await authTelegramWidget(user)
      if (!res.ok) {
        setError(loginErrorMessage(res.status))
        return
      }
      let accessToken: string | null = null
      try {
        const data = (await res.json()) as { access_token?: string }
        accessToken =
          typeof data.access_token === 'string' && data.access_token.trim()
            ? data.access_token.trim()
            : null
      } catch {
        accessToken = null
      }
      if (!accessToken) {
        setError('Ответ сервера без токена доступа.')
        return
      }
      writeAccessToken(accessToken)
      writeAuthSessionFlag(true)
      completeLogin()
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Не удалось войти. Проверьте соединение и повторите.')
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="min-h-dvh bg-(--tgui--bg_color) px-4 py-12 text-(--tgui--text_color)">
      <div className="mx-auto max-w-md">
        <Title weight="2" className="text-center">
          Filmony
        </Title>
        <p className="mt-4 text-center text-sm text-(--tgui--hint_color)">
          Войдите через Telegram, чтобы пользоваться лентой, профилем и оценками.
        </p>
        <Section className="mt-8 flex justify-center">
          <TelegramLoginWidget botUsername={botUsername} onAuth={(user) => void handleAuth(user)} />
        </Section>
        {busy ? (
          <p className="mt-4 text-center text-sm text-(--tgui--hint_color)">Вход…</p>
        ) : null}
        {error != null ? (
          <p className="mt-4 text-center text-sm text-(--tgui--destructive_text_color)">{error}</p>
        ) : null}
      </div>
    </div>
  )
}
