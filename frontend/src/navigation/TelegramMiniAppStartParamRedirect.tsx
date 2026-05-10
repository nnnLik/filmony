import { isTMA } from '@telegram-apps/sdk'
import { useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'

function readTelegramStartParam(): string | undefined {
  const fromUnsafe = window.Telegram?.WebApp?.initDataUnsafe?.start_param?.trim()
  if (fromUnsafe) {
    return fromUnsafe
  }
  return new URLSearchParams(window.location.search).get('tgWebAppStartParam')?.trim() || undefined
}

export function TelegramMiniAppStartParamRedirect() {
  const navigate = useNavigate()
  const ran = useRef(false)

  useEffect(() => {
    if (!isTMA() || ran.current) {
      return
    }
    const sp = readTelegramStartParam()
    if (sp == null || sp === '') {
      return
    }
    const m = /^c(\d+)$/i.exec(sp)
    if (m == null) {
      return
    }
    const cardId = Number(m[1])
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
  }, [navigate])

  return null
}
