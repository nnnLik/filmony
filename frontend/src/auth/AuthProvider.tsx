import { isTMA, retrieveRawInitData } from '@telegram-apps/sdk'
import { type ReactNode, useEffect, useMemo, useState } from 'react'

import { authTelegram } from '../api/profileApi'
import { AuthStateContext, type AuthStatus } from './auth-context'
import { clearMyProfileBundleCache } from '../lib/myProfileBundleCache'
import { readAuthSessionFlag, writeAuthSessionFlag } from '../lib/filmonySession'

function sdkInitDataRaw(): string {
  try {
    const v = retrieveRawInitData()
    return (typeof v === 'string' ? v : String(v ?? '')).trim()
  } catch {
    return ''
  }
}

function resolveInitDataRaw(): string {
  const fromSdk = sdkInitDataRaw()
  const fromWebApp = window.Telegram?.WebApp?.initData?.trim() ?? ''
  return fromSdk || fromWebApp
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<AuthStatus>(() => {
    if (!isTMA()) {
      return { kind: 'skipped' }
    }
    if (readAuthSessionFlag()) {
      return { kind: 'ready' }
    }
    return { kind: 'loading' }
  })

  useEffect(() => {
    if (!isTMA()) {
      return
    }

    let alive = true

    void (async () => {
      // Дождаться кадра: после init() и в StrictMode initData в WebApp может появиться не синхронно.
      await new Promise<void>((resolve) => {
        requestAnimationFrame(() => resolve())
      })
      if (!alive) {
        return
      }

      const raw = resolveInitDataRaw()
      if (!raw) {
        if (alive) {
          writeAuthSessionFlag(false)
          clearMyProfileBundleCache()
          setState({
            kind: 'error',
            message: 'Пустой initData — откройте приложение из Telegram.',
          })
        }
        return
      }

      try {
        const res = await authTelegram(raw)
        if (!alive) {
          return
        }
        if (!res.ok) {
          const t = await res.text()
          writeAuthSessionFlag(false)
          clearMyProfileBundleCache()
          setState({
            kind: 'error',
            message: t.trim() || `Ошибка входа (HTTP ${res.status})`,
          })
          return
        }
        writeAuthSessionFlag(true)
        setState({ kind: 'ready' })
      } catch (e) {
        if (!alive) {
          return
        }
        writeAuthSessionFlag(false)
        clearMyProfileBundleCache()
        setState({
          kind: 'error',
          message: e instanceof Error ? e.message : 'Сеть недоступна',
        })
      }
    })()

    return () => {
      alive = false
    }
  }, [])

  const value = useMemo(() => state, [state])
  return <AuthStateContext.Provider value={value}>{children}</AuthStateContext.Provider>
}
