export function FeedCardSkeleton() {
  return (
    <div
      className="flex animate-pulse flex-col gap-3 overflow-hidden rounded-2xl border border-(--tgui--divider_color) bg-[color-mix(in_srgb,var(--tgui--secondary_bg_color)_96%,transparent)] p-3 shadow-[0_10px_40px_-14px_rgba(0,0,0,0.45)]"
      aria-hidden
    >
      <div className="aspect-2/3 max-h-[min(52vw,14rem)] w-full rounded-xl bg-(--tgui--divider_color) sm:max-h-64" />
      <div className="flex items-center justify-between gap-2">
        <div className="size-[26px] shrink-0 rounded-full bg-(--tgui--divider_color)" />
        <div className="flex flex-1 flex-wrap justify-end gap-1">
          <div className="h-5 w-12 rounded-full bg-(--tgui--divider_color)" />
          <div className="h-5 w-12 rounded-full bg-(--tgui--divider_color)" />
        </div>
      </div>
      <div className="flex items-center justify-between">
        <div className="h-4 w-24 rounded bg-(--tgui--divider_color)" />
        <div className="h-3 w-5 rounded bg-(--tgui--divider_color)" />
      </div>
      {[0, 1].map((k) => (
        <div key={k} className="rounded-xl border border-(--tgui--divider_color) bg-(--tgui--bg_color) p-3">
          <div className="flex gap-2">
            <div className="size-7 shrink-0 rounded-full bg-(--tgui--divider_color)" />
            <div className="min-w-0 flex-1 space-y-2">
              <div className="flex gap-2">
                <div className="h-3 w-20 rounded bg-(--tgui--divider_color)" />
                <div className="h-3 w-10 rounded bg-(--tgui--divider_color)" />
              </div>
              <div className="h-3 w-full rounded bg-(--tgui--divider_color)" />
              <div className="h-3 w-2/3 rounded bg-(--tgui--divider_color)" />
            </div>
          </div>
        </div>
      ))}
      <div className="flex gap-1.5">
        <div className="h-9 min-w-0 flex-1 rounded-xl bg-(--tgui--divider_color)" />
        <div className="h-9 w-9 shrink-0 rounded-xl bg-(--tgui--divider_color)" />
      </div>
    </div>
  )
}
