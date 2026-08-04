export function SearchResultsSkeleton() {
  return (
    <div className="animate-pulse space-y-4 px-0" aria-hidden>
      <div className="space-y-2">
        {Array.from({ length: 3 }, (_, i) => (
          <div key={`user-${i}`} className="flex items-center gap-3 rounded-xl px-2.5 py-2">
            <div className="size-10 shrink-0 rounded-full bg-(--tgui--divider_color)" />
            <div className="h-4 w-32 rounded bg-(--tgui--divider_color)" />
          </div>
        ))}
      </div>
      <div className="space-y-2">
        {Array.from({ length: 4 }, (_, i) => (
          <div key={`card-${i}`} className="flex gap-3 rounded-xl px-2.5 py-2">
            <div className="aspect-2/3 h-16 shrink-0 rounded-lg bg-(--tgui--divider_color)" />
            <div className="flex flex-1 flex-col justify-center gap-2">
              <div className="h-4 w-3/4 rounded bg-(--tgui--divider_color)" />
              <div className="h-3 w-1/2 rounded bg-(--tgui--divider_color)" />
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
