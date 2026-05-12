export function RoutePageFallback() {
  return (
    <div
      className="flex min-h-[50dvh] flex-col items-center justify-center gap-2 px-4 text-center text-sm text-(--tgui--hint_color)"
      role="status"
      aria-live="polite"
      aria-busy="true"
    >
      <span className="inline-block size-8 animate-spin rounded-full border-2 border-(--tgui--divider_color) border-t-(--tgui--link_color)" />
      <span>Загрузка…</span>
    </div>
  )
}
