/**
 * Декоративное оформление постера в ленте, когда автор отметил карточку как любимую.
 * Без текста и пиктограмм «любимое» / сердца — только свет, рамка-видоискатель, лёгкий grain.
 */

const NOISE_BG = `url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 256 256'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.75' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E")`

const cornerBase =
  'pointer-events-none absolute z-[2] size-5 border-white/40 shadow-[0_0_14px_rgba(94,234,212,0.22)]'

export function FeedAuthorFavoritePosterChrome({ active }: { active: boolean }) {
  if (!active) {
    return null
  }

  return (
    <>
      <span className="sr-only">Карточка отмечена автором</span>
      {/* Засветка «зал» — виньетка */}
      <div
        className="pointer-events-none absolute inset-0 z-[1] bg-[radial-gradient(ellipse_88%_78%_at_50%_40%,transparent_25%,rgba(0,0,0,0.32)_100%)]"
        aria-hidden
      />
      {/* Внутреннее мятное свечение бренда */}
      <div
        className="pointer-events-none absolute inset-0 z-[1] shadow-[inset_0_0_48px_rgba(94,234,212,0.12)]"
        aria-hidden
      />
      {/* Лёгкий grain */}
      <div
        className="pointer-events-none absolute inset-0 z-[1] opacity-[0.085] mix-blend-overlay"
        style={{ backgroundImage: NOISE_BG }}
        aria-hidden
      />
      {/* Угловые скобы видоискателя */}
      <span
        className={`${cornerBase} left-2 top-2 rounded-tl-lg border-l-2 border-t-2`}
        aria-hidden
      />
      <span
        className={`${cornerBase} right-2 top-2 rounded-tr-lg border-r-2 border-t-2`}
        aria-hidden
      />
      <span
        className={`${cornerBase} bottom-2 left-2 rounded-bl-lg border-b-2 border-l-2`}
        aria-hidden
      />
      <span
        className={`${cornerBase} bottom-2 right-2 rounded-br-lg border-b-2 border-r-2`}
        aria-hidden
      />
    </>
  )
}
