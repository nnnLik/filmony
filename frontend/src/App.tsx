import {
  isMiniAppDark,
  isTMA,
  miniAppReady,
  type User,
} from '@telegram-apps/sdk'
import { useLaunchParams, useSignal } from '@telegram-apps/sdk-react'
import { useEffect, useState } from 'react'

type HelloResponse = { message: string }

function userDisplayName(user: User | undefined): string {
  if (user?.username) {
    return `@${user.username}`
  }
  const name = [user?.first_name, user?.last_name].filter(Boolean).join(' ')
  return name || '—'
}

function TelegramPanel() {
  const lp = useLaunchParams()
  const isDark = useSignal(isMiniAppDark)
  const user = lp.tgWebAppData?.user

  useEffect(() => {
    void miniAppReady()
  }, [])

  return (
    <section
      className={
        isDark ?? true
          ? 'rounded-2xl border border-white/10 bg-white/5 p-4'
          : 'rounded-2xl border border-slate-200 bg-white p-4 shadow-sm'
      }
    >
      <h2
        className={
          isDark ?? true
            ? 'text-xs font-medium uppercase tracking-wide text-slate-400'
            : 'text-xs font-medium uppercase tracking-wide text-slate-500'
        }
      >
        Пользователь Telegram
      </h2>
      <p
        className={
          (isDark ?? true ? 'text-white ' : 'text-slate-900 ') +
          'mt-2 text-lg font-semibold'
        }
      >
        {userDisplayName(user)}
      </p>
      {user?.id != null && (
        <p
          className={
            (isDark ?? true ? 'text-slate-500 ' : 'text-slate-400 ') +
            'mt-1 font-mono text-xs'
          }
        >
          id: {user.id}
        </p>
      )}
    </section>
  )
}

function OutsideTelegramPanel() {
  return (
    <section className="rounded-2xl border border-white/10 bg-white/5 p-4">
      <h2 className="text-xs font-medium uppercase tracking-wide text-slate-400">
        Пользователь Telegram
      </h2>
      <p className="mt-2 text-sm text-slate-300">
        Данные пользователя доступны только внутри Telegram Mini App (аналог{' '}
        <code className="rounded bg-black/30 px-1 py-0.5 text-xs">
          Telegram.WebApp.initDataUnsafe.user
        </code>
        ).
      </p>
    </section>
  )
}

export default function App() {
  const [hello, setHello] = useState<string | null>(null)
  const [helloError, setHelloError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false
    void (async () => {
      try {
        const res = await fetch('/api/hello')
        if (!res.ok) {
          throw new Error(`HTTP ${res.status}`)
        }
        const data = (await res.json()) as HelloResponse
        if (!cancelled) {
          setHello(data.message)
          setHelloError(null)
        }
      } catch (e) {
        if (!cancelled) {
          setHello(null)
          setHelloError(e instanceof Error ? e.message : 'Ошибка запроса')
        }
      }
    })()
    return () => {
      cancelled = true
    }
  }, [])

  return (
    <div className="min-h-dvh bg-[#0e1621] text-slate-100">
      <div className="mx-auto flex max-w-md flex-col gap-6 px-4 py-10">
        <header>
          <h1 className="text-2xl font-bold tracking-tight text-white">Filmony</h1>
          <p className="mt-1 text-sm text-slate-400">Telegram Mini App</p>
        </header>

        {isTMA() ? <TelegramPanel /> : <OutsideTelegramPanel />}

        <section className="rounded-2xl border border-[#3390ec]/25 bg-[#3390ec]/10 p-4">
          <h2 className="text-xs font-medium uppercase tracking-wide text-[#7ab8f0]">
            Ответ бэкенда <span className="font-mono text-slate-500">GET /api/hello</span>
          </h2>
          {helloError != null ? (
            <p className="mt-2 text-sm text-red-400">Не удалось загрузить: {helloError}</p>
          ) : (
            <p className="mt-2 text-base text-slate-100">{hello ?? 'Загрузка…'}</p>
          )}
        </section>
      </div>
    </div>
  )
}
