'use client'

import Image from 'next/image'
import { User, Users, Smile, BatteryLow, Laugh, Frown } from 'lucide-react'
import { Movie } from '@/lib/types'
import { RatingBadge } from './rating-badge'
import { cn } from '@/lib/utils'

interface MovieCardProps {
  movie: Movie
  onClick: () => void
}

export function MovieCard({ movie, onClick }: MovieCardProps) {
  return (
    <button
      onClick={onClick}
      className="w-full bg-card rounded-xl p-4 flex gap-4 text-left transition-all active:scale-[0.98] hover:bg-muted/50"
    >
      <div className="relative w-20 h-28 rounded-lg overflow-hidden flex-shrink-0 bg-muted">
        <Image
          src={movie.poster}
          alt={movie.title}
          fill
          className="object-cover"
        />
      </div>
      
      <div className="flex-1 min-w-0 flex flex-col">
        <div className="flex items-start justify-between gap-2">
          <div className="min-w-0">
            <h3 className="font-medium text-foreground truncate text-base leading-tight">
              {movie.title}
            </h3>
            <p className="text-sm text-muted-foreground mt-0.5">{movie.year}</p>
          </div>
          {movie.rating && <RatingBadge rating={movie.rating} size="lg" />}
        </div>
        
        <div className="flex items-center gap-2 mt-3">
          {movie.company && (
            <TagIcon type={movie.company === 'alone' ? 'alone' : 'friends'} />
          )}
          {movie.moodBefore && (
            <TagIcon type={movie.moodBefore === 'happy' ? 'happy' : 'tired'} />
          )}
          {movie.moodAfter && (
            <TagIcon type={movie.moodAfter === 'laughed' ? 'laughed' : 'cried'} />
          )}
        </div>
        
        {movie.friendRatings.length > 0 && (
          <div className="flex items-center gap-1.5 mt-auto pt-2">
            <div className="flex -space-x-2">
              {movie.friendRatings.slice(0, 4).map((friend) => (
                <div
                  key={friend.id}
                  className="relative w-6 h-6 rounded-full overflow-hidden border-2 border-card"
                >
                  <Image
                    src={friend.avatar}
                    alt={friend.name}
                    fill
                    className="object-cover"
                  />
                </div>
              ))}
            </div>
            <div className="flex items-center gap-1 text-xs text-muted-foreground">
              {movie.friendRatings.slice(0, 3).map((friend, i) => (
                <span key={friend.id} className={cn(i > 0 && 'before:content-[",_"]')}>
                  {friend.rating}
                </span>
              ))}
            </div>
          </div>
        )}
      </div>
    </button>
  )
}

function TagIcon({ type }: { type: 'alone' | 'friends' | 'happy' | 'tired' | 'laughed' | 'cried' }) {
  const iconClass = 'w-4 h-4 text-muted-foreground'
  const wrapperClass = 'p-1.5 rounded-lg bg-muted/60'
  
  const icons = {
    alone: <User className={iconClass} />,
    friends: <Users className={iconClass} />,
    happy: <Smile className={iconClass} />,
    tired: <BatteryLow className={iconClass} />,
    laughed: <Laugh className={iconClass} />,
    cried: <Frown className={iconClass} />,
  }
  
  return <div className={wrapperClass}>{icons[type]}</div>
}
