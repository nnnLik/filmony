'use client'

import { cn } from '@/lib/utils'

interface RatingBadgeProps {
  rating: number
  size?: 'sm' | 'md' | 'lg'
  className?: string
}

const ratingColors: Record<number, string> = {
  1: 'bg-red-500 text-white',
  2: 'bg-red-400 text-white',
  3: 'bg-orange-500 text-white',
  4: 'bg-orange-400 text-white',
  5: 'bg-yellow-500 text-foreground',
  6: 'bg-yellow-400 text-foreground',
  7: 'bg-lime-500 text-foreground',
  8: 'bg-green-500 text-white',
  9: 'bg-green-600 text-white',
  10: 'bg-emerald-600 text-white',
}

const sizeClasses = {
  sm: 'w-6 h-6 text-xs',
  md: 'w-9 h-9 text-sm font-semibold',
  lg: 'w-14 h-14 text-xl font-bold',
}

export function RatingBadge({ rating, size = 'md', className }: RatingBadgeProps) {
  return (
    <div
      className={cn(
        'rounded-full flex items-center justify-center',
        ratingColors[rating] || 'bg-muted text-muted-foreground',
        sizeClasses[size],
        className
      )}
    >
      {rating}
    </div>
  )
}
