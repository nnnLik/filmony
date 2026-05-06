import { Button, Section } from '@telegram-apps/telegram-ui'
import { isTMA, miniAppReady } from '@telegram-apps/sdk'
import { useLaunchParams } from '@telegram-apps/sdk-react'
import { useEffect } from 'react'

function TelegramHint() {
  const lp = useLaunchParams()
  const u = lp.tgWebAppData?.user
  const line =
    u?.username != null
      ? `@${u.username}`
      : [u?.first_name, u?.last_name].filter(Boolean).join(' ') || 'гость'

  useEffect(() => {
    void miniAppReady()
  }, [])

  if (!isTMA()) {
    return (
      <p className="text-center text-sm text-(--tgui--hint_color)">
        Откройте мини-приложение в Telegram — здесь появится ваша лента.
      </p>
    )
  }

  return (
    <p className="text-center text-sm text-(--tgui--hint_color)">
      Вы вошли как <span className="font-medium text-(--tgui--text_color)">{line}</span>
    </p>
  )
}

export function FeedPage() {
  return (
    <div className="min-h-full">
      <header className="sticky top-0 z-20 border-b border-(--tgui--divider_color) bg-(--tgui--bg_color)/95 backdrop-blur-md">
        <div className="flex items-center justify-between px-4 py-3">
          <div>
            <h1 className="text-lg font-semibold tracking-tight">Filmony</h1>
          </div>
          <Button mode="gray" disabled title="Скоро">
            +
          </Button>
        </div>
      </header>

      <main className="px-4 py-6">
        <Section header="Лента">
          <div className="flex flex-col items-center gap-4 px-3 py-10">
            <p className="text-center text-sm leading-relaxed text-(--tgui--hint_color)">
              Пока нет карточек в ленте. Когда появится бэкенд ленты, здесь будут оценки друзей и редкие вкидки от
              похожих по вкусу.
            </p>
            <Button stretched disabled>
              Добавить фильм (скоро)
            </Button>
          </div>
        </Section>

        <div className="mt-6">
          <TelegramHint />
        </div>
      </main>
    </div>
  )
}
