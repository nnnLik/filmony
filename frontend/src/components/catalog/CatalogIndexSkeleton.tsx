export function CatalogIndexSkeleton() {
  return (
    <div className="animate-pulse space-y-2 px-4 py-3" aria-hidden>
      {Array.from({ length: 8 }, (_, i) => (
        <div
          key={i}
          className="flex items-center justify-between rounded-xl border border-(--tgui--divider_color) px-3 py-3"
        >
          <div className="h-4 w-2/5 rounded bg-(--tgui--divider_color)" />
          <div className="h-4 w-12 rounded bg-(--tgui--divider_color)" />
        </div>
      ))}
    </div>
  )
}
