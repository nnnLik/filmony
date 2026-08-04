import { ChevronLeft } from 'lucide-react'
import { Link, useNavigate } from 'react-router'

type StickyBackHeaderProps = {
  title: string
  backHref?: string
  onBack?: () => void
  trailing?: React.ReactNode
  className?: string
}

export function StickyBackHeader({
  title,
  backHref,
  onBack,
  trailing,
  className,
}: StickyBackHeaderProps) {
  const navigate = useNavigate()

  const backControl =
    backHref != null ? (
      <Link
        to={backHref}
        className="flex size-9 items-center justify-center rounded-full text-(--tgui--text_color) no-underline outline-none active:opacity-80"
        aria-label="Назад"
      >
        <ChevronLeft className="block size-5" strokeWidth={1.75} aria-hidden />
      </Link>
    ) : (
      <button
        type="button"
        className="flex size-9 items-center justify-center rounded-full text-(--tgui--text_color) outline-none active:opacity-80"
        aria-label="Назад"
        onClick={() => {
          if (onBack != null) {
            onBack()
          } else {
            void navigate(-1)
          }
        }}
      >
        <ChevronLeft className="block size-5" strokeWidth={1.75} aria-hidden />
      </button>
    )

  return (
    <header
      className={`sticky top-0 z-20 flex items-center gap-2 border-b border-(--tgui--divider_color) bg-[color-mix(in_srgb,var(--tgui--bg_color)_88%,transparent)] px-2 py-2 backdrop-blur-md ${className ?? ''}`}
    >
      {backControl}
      <span className="min-w-0 flex-1 truncate text-sm font-medium">{title}</span>
      {trailing != null ? <div className="shrink-0">{trailing}</div> : null}
    </header>
  )
}
