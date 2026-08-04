export function DetailPageSkeleton() {
  return (
    <div className="animate-pulse px-4 pb-10 pt-4" aria-hidden>
      <div className="aspect-2/3 max-h-[min(60vw,18rem)] w-full rounded-2xl bg-(--tgui--divider_color)" />
      <div className="mt-4 space-y-2">
        <div className="h-6 w-3/4 rounded bg-(--tgui--divider_color)" />
        <div className="h-4 w-1/3 rounded bg-(--tgui--divider_color)" />
      </div>
      <div className="mt-4 flex gap-2">
        <div className="h-9 flex-1 rounded-xl bg-(--tgui--divider_color)" />
        <div className="h-9 flex-1 rounded-xl bg-(--tgui--divider_color)" />
      </div>
      <div className="mt-6 space-y-3">
        <div className="h-4 w-full rounded bg-(--tgui--divider_color)" />
        <div className="h-4 w-5/6 rounded bg-(--tgui--divider_color)" />
        <div className="h-4 w-2/3 rounded bg-(--tgui--divider_color)" />
      </div>
    </div>
  )
}
