import { useMemo, useState } from 'react'

import { resolveApiMediaUrl } from '../../../lib/resolveApiMediaUrl'

export function ReactionThumb({
  src,
  className,
  roundedClassName = 'rounded-lg',
}: {
  src: string
  className: string
  roundedClassName?: string
}) {
  const [failed, setFailed] = useState(false)

  const resolved = useMemo(() => resolveApiMediaUrl(src), [src])

  if (failed) {
    return (
      <div
        className={`animate-pulse bg-[color-mix(in_srgb,var(--tgui--divider_color)_45%,transparent)] ${roundedClassName} ${className}`}
        aria-hidden
      />
    )
  }

  return (
    <img
      src={resolved}
      alt=""
      className={`${roundedClassName} border-0 object-cover outline-none ${className}`}
      onError={() => setFailed(true)}
    />
  )
}
