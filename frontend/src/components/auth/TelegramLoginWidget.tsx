import { useEffect, useRef } from 'react'

import type { TelegramWidgetAuthPayload } from '../../api/profileApi'

const CALLBACK_NAME = '__filmonyTelegramOnAuth'

type TelegramWidgetUser = {
  id: number
  first_name?: string
  last_name?: string
  username?: string
  photo_url?: string
  auth_date: number
  hash: string
}

export type TelegramLoginWidgetProps = {
  botUsername: string
  onAuth: (user: TelegramWidgetAuthPayload) => void
  className?: string
}

declare global {
  interface Window {
    __filmonyTelegramOnAuth?: (user: TelegramWidgetUser) => void
  }
}

function mapToPayload(user: TelegramWidgetUser): TelegramWidgetAuthPayload {
  const payload: TelegramWidgetAuthPayload = {
    id: user.id,
    auth_date: user.auth_date,
    hash: user.hash,
  }
  if (user.first_name) {
    payload.first_name = user.first_name
  }
  if (user.last_name) {
    payload.last_name = user.last_name
  }
  if (user.username) {
    payload.username = user.username
  }
  if (user.photo_url) {
    payload.photo_url = user.photo_url
  }
  return payload
}

export function TelegramLoginWidget({ botUsername, onAuth, className }: TelegramLoginWidgetProps) {
  const containerRef = useRef<HTMLDivElement>(null)
  const onAuthRef = useRef(onAuth)

  useEffect(() => {
    onAuthRef.current = onAuth
  }, [onAuth])

  useEffect(() => {
    const container = containerRef.current
    if (!container || !botUsername) {
      return
    }

    window.__filmonyTelegramOnAuth = (user: TelegramWidgetUser) => {
      onAuthRef.current(mapToPayload(user))
    }

    const script = document.createElement('script')
    script.src = 'https://telegram.org/js/telegram-widget.js?22'
    script.async = true
    script.setAttribute('data-telegram-login', botUsername)
    script.setAttribute('data-size', 'large')
    script.setAttribute('data-radius', '8')
    script.setAttribute('data-request-access', 'write')
    // telegram-widget.js wraps data-onauth as (function(user){ <attr> }); bare name does not invoke the callback
    script.setAttribute('data-onauth', `${CALLBACK_NAME}(user)`)
    container.replaceChildren()
    container.appendChild(script)

    return () => {
      delete window.__filmonyTelegramOnAuth
      script.remove()
    }
  }, [botUsername])

  if (!botUsername) {
    return (
      <p className={`text-sm text-(--tgui--destructive_text_color) ${className ?? ''}`}>
        Бот не настроен (VITE_TELEGRAM_BOT_USERNAME)
      </p>
    )
  }

  return <div ref={containerRef} className={className} />
}
