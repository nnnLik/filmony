import { isTMA, retrieveRawInitData } from '@telegram-apps/sdk'
import { type ReactNode, useEffect, useMemo, useState } from 'react'

import { apiFetch } from '../api/client'
import { authTelegram } from '../api/profileApi'
import { AuthStateContext, type AuthStatus } from './auth-context'
import { clearMyProfileBundleCache } from '../lib/myProfileBundleCache'
import {
  readAccessToken,
  readAuthSessionFlag,
  writeAccessToken,
  writeAuthSessionFlag,
} from '../lib/filmonySession'

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

const authBootstrapGeneration = { current: 0 }

async function waitForInitDataRaw(
  maxFrames: number,
  isCurrent: () => boolean
): Promise<string> {
  for (let i = 0; i < maxFrames; i++) {
    if (!isCurrent()) {
      return ''
    }
    const raw = resolveInitDataRaw()
    if (raw) {
      return raw
    }
    await new Promise<void>((resolve) => {
      requestAnimationFrame(() => resolve())
    })
  }
  return resolveInitDataRaw()
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<AuthStatus>(() => {
    if (!isTMA()) {
      return { kind: 'skipped' }
    }
    if (readAuthSessionFlag() && readAccessToken()) {
      return { kind: 'ready' }
    }
    if (readAuthSessionFlag() && !readAccessToken()) {
      writeAuthSessionFlag(false)
    }
    return { kind: 'loading' }
  })

  useEffect(() => {
    if (!isTMA()) {
      return
    }

    // Уже есть JWT в storage — не дублируем POST /auth/telegram при каждом mount.
    if (readAccessToken()) {
      writeAuthSessionFlag(true)
      return
    }

    const runId = ++authBootstrapGeneration.current

    void (async () => {
      await new Promise<void>((resolve) => {
        requestAnimationFrame(() => resolve())
      })
      if (runId !== authBootstrapGeneration.current) {
        return
      }

      const tryResumeFromCookie = async (): Promise<boolean> => {
        try {
          const probe = await apiFetch('/api/me/profile', {
            method: 'GET',
            headers: { Accept: 'application/json' },
          })
          if (runId !== authBootstrapGeneration.current) {
            return false
          }
          if (!probe.ok) {
            return false
          }
          writeAuthSessionFlag(true)
          setState({ kind: 'ready' })
          return true
        } catch {
          return false
        }
      }

      // Сессия по HttpOnly cookie: бэкенд уже знает пользователя, Bearer в storage не нужен.
      if (await tryResumeFromCookie()) {
        return
      }

      const raw = await waitForInitDataRaw(16, () => runId === authBootstrapGeneration.current)
      if (runId !== authBootstrapGeneration.current) {
        return
      }

      if (!raw) {
        if (await tryResumeFromCookie()) {
          return
        }
        writeAuthSessionFlag(false)
        writeAccessToken(null)
        clearMyProfileBundleCache()
        setState({
          kind: 'error',
          message: 'Пустой initData — откройте приложение из Telegram.',
        })
        return
      }

      try {
        const res = await authTelegram(raw)
        if (runId !== authBootstrapGeneration.current) {
          return
        }
        if (!res.ok) {
          const t = await res.text()
          writeAuthSessionFlag(false)
          writeAccessToken(null)
          clearMyProfileBundleCache()
          setState({
            kind: 'error',
            message: t.trim() || `Ошибка входа (HTTP ${res.status})`,
          })
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
          writeAuthSessionFlag(false)
          writeAccessToken(null)
          clearMyProfileBundleCache()
          setState({
            kind: 'error',
            message: 'Ответ входа без access_token',
          })
          return
        }
        writeAccessToken(accessToken)
        writeAuthSessionFlag(true)
        setState({ kind: 'ready' })
      } catch (e) {
        if (runId !== authBootstrapGeneration.current) {
          return
        }
        writeAuthSessionFlag(false)
        writeAccessToken(null)
        clearMyProfileBundleCache()
        setState({
          kind: 'error',
          message: e instanceof Error ? e.message : 'Сеть недоступна',
        })
      }
    })()
  }, [])

  const value = useMemo(() => state, [state])
  return <AuthStateContext.Provider value={value}>{children}</AuthStateContext.Provider>
}
