import { Button, Section } from '@telegram-apps/telegram-ui'
import { isTMA, miniAppReady } from '@telegram-apps/sdk'
import { useLaunchParams } from '@telegram-apps/sdk-react'
import { useEffect } from 'react'
import { Link } from 'react-router-dom'

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
      <p className="filmony-text-panel text-center text-sm text-(--tgui--hint_color)">
        Откройте мини-приложение в Telegram — здесь появится ваша лента.
      </p>
    )
  }

  return (
    <p className="filmony-text-panel text-center text-sm text-(--tgui--hint_color)">
      Вы вошли как <span className="font-medium text-(--tgui--text_color)">{line}</span>
    </p>
  )
}

export function FeedPage() {
  return (
    <div className="min-h-full">
      <header className="sticky top-0 z-20 border-b border-(--tgui--divider_color) bg-[color-mix(in_srgb,var(--tgui--bg_color)_88%,transparent)] backdrop-blur-md">
        <div className="flex items-center justify-between px-4 py-3">
          <div>
            <h1 className="bg-gradient-to-r from-[var(--filmony-mint,#5eead4)] via-[var(--filmony-text,#e8f0f7)] to-[var(--filmony-amber,#e8b86d)] bg-clip-text text-lg font-semibold tracking-tight text-transparent">
              Filmony
            </h1>
          </div>
          <Link to="/cards/new" aria-label="Добавить фильм" className="no-underline">
            <Button mode="gray">+</Button>
          </Link>
        </div>
      </header>

      <main className="px-4 py-6">
        <Section header="Лента">
          <div className="flex flex-col items-center gap-4 px-3 py-10">
            <p className="filmony-text-panel text-center text-sm leading-relaxed text-(--tgui--hint_color)">
              Пока нет карточек в ленте. Когда появится бэкенд ленты, здесь будут оценки друзей и редкие вкидки от
              похожих по вкусу.
            </p>
            <Link to="/cards/new" className="w-full no-underline">
              <Button stretched>Добавить фильм</Button>
            </Link>
          </div>
        </Section>

        <div className="mt-6">
          <TelegramHint />
        </div>
      </main>
    </div>
  )
}
