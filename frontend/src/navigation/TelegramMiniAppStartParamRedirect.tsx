import { isTMA } from '@telegram-apps/sdk'
import { useEffect, useRef } from 'react'
import { useNavigate } from 'react-router'

import { useAuthStatus } from '../auth/useAuthStatus'
import {
  markStartParamHandled,
  readTelegramStartParamSync,
  resolveStartParamToPath,
  startParamHandledKey,
} from '../lib/miniAppCardDeepLink'

export function TelegramMiniAppStartParamRedirect() {
  const navigate = useNavigate()
  const auth = useAuthStatus()
  const ran = useRef(false)

  useEffect(() => {
    if (!isTMA() || ran.current || auth.kind !== 'ready') {
      return
    }

    const startParam = readTelegramStartParamSync()
    if (startParam == null || startParam === '') {
      return
    }

    const resolved = resolveStartParamToPath(startParam)
    if (resolved == null) {
      return
    }

    const key = startParamHandledKey(startParam)
    if (sessionStorage.getItem(key) === '1') {
      return
    }

    ran.current = true
    markStartParamHandled(startParam)
    void navigate(resolved.path, {
      replace: true,
      state: resolved.state,
    })
  }, [navigate, auth.kind])

  return null
}
