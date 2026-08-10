import { isTMA, retrieveRawInitData } from '@telegram-apps/sdk'
import { type ReactNode, useCallback, useEffect, useMemo, useState } from 'react'

import { runAuthBootstrap } from './authBootstrap'
import { AuthActionsContext } from './auth-actions-context'
import { AuthStateContext, type AuthStatus } from './auth-context'
import {
  readAccessToken,
  readAuthSessionFlag,
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

/** Cold notification/deeplink opens can inject initData after the first paint. */
const INIT_DATA_FAST_FRAMES = 30
const INIT_DATA_POLL_MS = 50

function signalTelegramWebAppReady(): void {
  try {
    window.Telegram?.WebApp?.ready?.()
  } catch {
    /* noop */
  }
}

async function waitForInitDataRaw(
  maxWaitMs: number,
  isCurrent: () => boolean
): Promise<string> {
  for (let i = 0; i < INIT_DATA_FAST_FRAMES; i++) {
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

  const deadline = Date.now() + maxWaitMs
  while (isCurrent() && Date.now() < deadline) {
    const raw = resolveInitDataRaw()
    if (raw) {
      return raw
    }
    await new Promise<void>((resolve) => {
      setTimeout(resolve, INIT_DATA_POLL_MS)
    })
  }
  return resolveInitDataRaw()
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<AuthStatus>(() => {
    if (readAuthSessionFlag() && readAccessToken()) {
      return { kind: 'loading' }
    }
    if (readAuthSessionFlag() && !readAccessToken()) {
      writeAuthSessionFlag(false)
    }
    return { kind: 'loading' }
  })

  useEffect(() => {
    const runId = ++authBootstrapGeneration.current
    const environment = isTMA() ? 'tma' : 'browser'

    void (async () => {
      if (isTMA()) {
        signalTelegramWebAppReady()
        await new Promise<void>((resolve) => {
          requestAnimationFrame(() => resolve())
        })
        if (runId !== authBootstrapGeneration.current) {
          return
        }
      }

      await runAuthBootstrap({
        runId,
        isCurrent: () => runId === authBootstrapGeneration.current,
        setState,
        waitForInitDataRaw,
        environment,
      })
    })()
  }, [])

  const value = useMemo(() => state, [state])
  const completeLogin = useCallback(() => {
    setState({ kind: 'ready' })
  }, [])
  const actions = useMemo(() => ({ completeLogin }), [completeLogin])

  return (
    <AuthActionsContext.Provider value={actions}>
      <AuthStateContext.Provider value={value}>{children}</AuthStateContext.Provider>
    </AuthActionsContext.Provider>
  )
}
