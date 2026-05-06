import { Button, Section } from '@telegram-apps/telegram-ui'
import { Link } from 'react-router-dom'

export function FeedPage() {
  return (
    <div className="min-h-full">
      <header className="sticky top-0 z-20 border-b border-(--tgui--divider_color) bg-[color-mix(in_srgb,var(--tgui--bg_color)_88%,transparent)] backdrop-blur-md">
        <div className="flex items-center justify-between px-4 py-3">
          <div>
            <h1 className="bg-linear-to-r from-(--filmony-mint,#5eead4) via-(--filmony-text,#e8f0f7) to-(--filmony-amber,#e8b86d) bg-clip-text text-lg font-semibold tracking-tight text-transparent">
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
            <Link to="/cards/new" className="w-full no-underline">
              <Button stretched>Добавить фильм</Button>
            </Link>
          </div>
        </Section>
      </main>
    </div>
  )
}
