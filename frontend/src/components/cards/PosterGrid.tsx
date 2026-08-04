import type { ReactNode } from 'react'

export type PosterGridProps = {
  children: ReactNode
  className?: string
}

export function PosterGrid({ children, className = '' }: PosterGridProps) {
  return <div className={`grid grid-cols-3 gap-2 ${className}`.trim()}>{children}</div>
}
