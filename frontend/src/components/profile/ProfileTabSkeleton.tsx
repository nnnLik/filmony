export function ProfileTabSkeleton() {
  return (
    <div className="animate-pulse px-4 py-3" aria-hidden>
      <div className="mb-4 flex gap-2">
        <div className="h-8 w-20 rounded-full bg-(--tgui--divider_color)" />
        <div className="h-8 w-24 rounded-full bg-(--tgui--divider_color)" />
        <div className="h-8 w-16 rounded-full bg-(--tgui--divider_color)" />
      </div>
      <div className="grid grid-cols-3 gap-2">
        {Array.from({ length: 6 }, (_, i) => (
          <div key={i} className="aspect-2/3 rounded-xl bg-(--tgui--divider_color)" />
        ))}
      </div>
    </div>
  )
}
