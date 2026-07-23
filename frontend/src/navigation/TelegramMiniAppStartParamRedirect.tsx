import { isTMA } from '@telegram-apps/sdk'
import { useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'

import { useAuthStatus } from '../auth/useAuthStatus'
import { parseMiniAppWatchlistStartParam, parseMiniAppTasteQuizStartParam } from '../lib/miniAppCardDeepLink'

function readTelegramStartParam(): string | undefined {
  const fromUnsafe = window.Telegram?.WebApp?.initDataUnsafe?.start_param?.trim()
  if (fromUnsafe) {
    return fromUnsafe
  }
  return new URLSearchParams(window.location.search).get('tgWebAppStartParam')?.trim() || undefined
}

export function TelegramMiniAppStartParamRedirect() {
  const navigate = useNavigate()
  const auth = useAuthStatus()
  const ran = useRef(false)

  useEffect(() => {
    if (!isTMA() || ran.current || auth.kind !== 'ready') {
      return
    }
    const sp = readTelegramStartParam()
    if (sp == null || sp === '') {
      return
    }

    const watchlistCardId = parseMiniAppWatchlistStartParam(sp)
    if (watchlistCardId != null) {
      const key = `filmony.handled_start_param.${sp}`
      if (sessionStorage.getItem(key) === '1') {
        return
      }
      ran.current = true
      sessionStorage.setItem(key, '1')
      void navigate('/profile?movies=watchlist', {
        replace: true,
        state: {
          watchlistInviteCardId: watchlistCardId,
        },
      })
      return
    }

    const tasteQuizToken = parseMiniAppTasteQuizStartParam(sp)
    if (tasteQuizToken != null) {
      const key = `filmony.handled_start_param.${sp}`
      if (sessionStorage.getItem(key) === '1') {
        return
      }
      ran.current = true
      sessionStorage.setItem(key, '1')
      void navigate(`/taste-quiz/invite/${encodeURIComponent(tasteQuizToken)}`, {
        replace: true,
      })
      return
    }

    const cardMatch = /^c(\d+)$/i.exec(sp)
    if (cardMatch != null) {
      const cardId = Number(cardMatch[1])
      if (!Number.isInteger(cardId) || cardId < 1) {
        return
      }
      const key = `filmony.handled_start_param.${sp}`
      if (sessionStorage.getItem(key) === '1') {
        return
      }
      ran.current = true
      sessionStorage.setItem(key, '1')
      void navigate(`/cards/${cardId}`, {
        replace: true,
        state: { cardEntry: 'telegram_start_param' as const },
      })
      return
    }

    const postMatch = /^p(\d+)$/i.exec(sp)
    if (postMatch != null) {
      const postId = Number(postMatch[1])
      if (!Number.isInteger(postId) || postId < 1) {
        return
      }
      const key = `filmony.handled_start_param.${sp}`
      if (sessionStorage.getItem(key) === '1') {
        return
      }
      ran.current = true
      sessionStorage.setItem(key, '1')
      void navigate(`/feed-posts/${postId}`, {
        replace: true,
        state: { fromFeed: true },
      })
    }
  }, [navigate, auth.kind])

  return null
}
