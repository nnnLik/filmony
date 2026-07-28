import { apiFetch, apiFetchCredentialsOnly } from '../api/client'
import { authTelegram } from '../api/profileApi'
import { clearMyProfileBundleCache } from '../lib/myProfileBundleCache'
import { clearMovieCardTagStatsSessionCaches } from '../lib/movieCardTagStatsStorage'
import { clearUserCardCategoriesSessionCaches } from '../lib/userCardCategoriesStorage'
import {
  readAccessToken,
  writeAccessToken,
  writeAuthSessionFlag,
} from '../lib/filmonySession'
import type { AuthStatus } from './auth-context'

export type AuthBootstrapDeps = {
  runId: number
  isCurrent: () => boolean
  setState: (status: AuthStatus) => void
  waitForInitDataRaw: (maxWaitMs: number, isCurrent: () => boolean) => Promise<string>
}

export async function runAuthBootstrap(deps: AuthBootstrapDeps): Promise<void> {
  const { runId, isCurrent, setState, waitForInitDataRaw } = deps

  const resumeWithStoredBearer = async (): Promise<boolean> => {
    const token = readAccessToken()
    if (!token) {
      return false
    }
    try {
      const probe = await apiFetch('/api/me', {
        method: 'GET',
        headers: {
          Accept: 'application/json',
          Authorization: `Bearer ${token}`,
        },
      })
      if (!isCurrent()) {
        return false
      }
      if (!probe.ok) {
        writeAuthSessionFlag(false)
        writeAccessToken(null)
        return false
      }
      writeAuthSessionFlag(true)
      setState({ kind: 'ready' })
      return true
    } catch {
      return false
    }
  }

  const tryResumeFromCookie = async (): Promise<boolean> => {
    try {
      const probe = await apiFetchCredentialsOnly('/api/me/profile', {
        method: 'GET',
      })
      if (!isCurrent()) {
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

  const initDataPromise = waitForInitDataRaw(4000, isCurrent)
  const bearerPromise = resumeWithStoredBearer()
  const cookiePromise = tryResumeFromCookie()

  if (await bearerPromise) {
    return
  }
  if (await cookiePromise) {
    return
  }

  const raw = await initDataPromise
  if (!isCurrent()) {
    return
  }

  if (!raw) {
    if (await tryResumeFromCookie()) {
      return
    }
    writeAuthSessionFlag(false)
    writeAccessToken(null)
    clearMyProfileBundleCache()
    clearMovieCardTagStatsSessionCaches()
    clearUserCardCategoriesSessionCaches()
    setState({
      kind: 'error',
      message: 'Пустой initData — откройте приложение из Telegram.',
    })
    return
  }

  try {
    const res = await authTelegram(raw)
    if (!isCurrent()) {
      return
    }
    if (!res.ok) {
      const t = await res.text()
      writeAuthSessionFlag(false)
      writeAccessToken(null)
      clearMyProfileBundleCache()
      clearMovieCardTagStatsSessionCaches()
      clearUserCardCategoriesSessionCaches()
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
      clearMovieCardTagStatsSessionCaches()
      clearUserCardCategoriesSessionCaches()
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
    if (!isCurrent()) {
      return
    }
    writeAuthSessionFlag(false)
    writeAccessToken(null)
    clearMyProfileBundleCache()
    clearMovieCardTagStatsSessionCaches()
    clearUserCardCategoriesSessionCaches()
    setState({
      kind: 'error',
      message: e instanceof Error ? e.message : 'Сеть недоступна',
    })
  }
