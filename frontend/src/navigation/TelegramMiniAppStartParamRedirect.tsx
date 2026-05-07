import { isTMA } from '@telegram-apps/sdk'
import { useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'

/**
 * Обрабатывает Direct Link Mini App: ``?startapp=c<card_id>`` → ``start_param`` в initData → маршрут ``/cards/:id``.
 */
export function TelegramMiniAppStartParamRedirect() {
  const navigate = useNavigate()
  const ran = useRef(false)

  useEffect(() => {
    if (!isTMA() || ran.current) {
      return
    }
    const sp = window.Telegram?.WebApp?.initDataUnsafe?.start_param?.trim()
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
    void navigate(`/cards/${cardId}`, { replace: true })
  }, [navigate])

  return null
}
