'use client'

import { useState } from 'react'
import Image from 'next/image'
import { ArrowLeft, User, Users, Smile, BatteryLow, Laugh, Frown, X, UserPlus, Send, Heart } from 'lucide-react'
import { Movie } from '@/lib/types'
import { RatingBadge } from '@/components/rating-badge'
import { cn } from '@/lib/utils'

interface MovieDetailScreenProps {
  movie: Movie
  onBack: () => void
  onUpdate: (movie: Movie) => void
}

export function MovieDetailScreen({ movie, onBack, onUpdate }: MovieDetailScreenProps) {
  const [currentMovie, setCurrentMovie] = useState(movie)
  const [newTag, setNewTag] = useState('')

  const updateMovie = (updates: Partial<Movie>) => {
    const updated = { ...currentMovie, ...updates }
    setCurrentMovie(updated)
    onUpdate(updated)
  }

  const handleAddTag = () => {
    if (newTag.trim() && currentMovie.customTags.length < 5) {
      updateMovie({ customTags: [...currentMovie.customTags, newTag.trim()] })
      setNewTag('')
    }
  }

  const handleRemoveTag = (index: number) => {
    updateMovie({ customTags: currentMovie.customTags.filter((_, i) => i !== index) })
  }

  return (
    <div className="min-h-screen bg-background pb-24">
      <header className="sticky top-0 z-10 bg-background/80 backdrop-blur-sm border-b border-border">
        <div className="max-w-md mx-auto px-4 py-3 flex items-center gap-3">
          <button
            onClick={onBack}
            className="w-10 h-10 rounded-full flex items-center justify-center hover:bg-muted transition-colors"
          >
            <ArrowLeft className="w-5 h-5" />
          </button>
          <h1 className="font-medium text-foreground truncate">{currentMovie.title}</h1>
        </div>
      </header>

      <main className="max-w-md mx-auto">
        {/* Poster */}
        <div className="relative w-full aspect-[2/3] max-h-80">
          <Image
            src={currentMovie.poster}
            alt={currentMovie.title}
            fill
            className="object-cover"
            priority
          />
          <div className="absolute inset-0 bg-gradient-to-t from-background via-transparent to-transparent" />
        </div>

        <div className="px-4 -mt-16 relative z-10">
          {/* Title & Year */}
          <h2 className="text-2xl font-bold text-foreground">{currentMovie.title}</h2>
          <p className="text-muted-foreground mt-1">{currentMovie.year}</p>

          {/* Rating Selector */}
          <div className="mt-6">
            <h3 className="text-sm font-medium text-muted-foreground mb-3">Твоя оценка</h3>
            <div className="flex items-center gap-2 flex-wrap">
              {[1, 2, 3, 4, 5, 6, 7, 8, 9, 10].map((num) => (
                <button
                  key={num}
                  onClick={() => updateMovie({ rating: num })}
                  className={cn(
                    'transition-transform active:scale-95',
                    currentMovie.rating === num && 'ring-2 ring-offset-2 ring-primary rounded-full'
                  )}
                >
                  <RatingBadge rating={num} size="md" />
                </button>
              ))}
            </div>
          </div>

          {/* Tags */}
          <div className="mt-8">
            <h3 className="text-sm font-medium text-muted-foreground mb-3">Теги</h3>
            
            {/* Company */}
            <div className="flex gap-2 mb-3">
              <TagButton
                active={currentMovie.company === 'alone'}
                onClick={() => updateMovie({ company: currentMovie.company === 'alone' ? null : 'alone' })}
                icon={<User className="w-4 h-4" />}
                label="Один"
              />
              <TagButton
                active={currentMovie.company === 'friends'}
                onClick={() => updateMovie({ company: currentMovie.company === 'friends' ? null : 'friends' })}
                icon={<Users className="w-4 h-4" />}
                label="С друзьями"
              />
            </div>

            {/* Mood Before */}
            <div className="flex gap-2 mb-3">
              <TagButton
                active={currentMovie.moodBefore === 'happy'}
                onClick={() => updateMovie({ moodBefore: currentMovie.moodBefore === 'happy' ? null : 'happy' })}
                icon={<Smile className="w-4 h-4" />}
                label="Весёлый"
              />
              <TagButton
                active={currentMovie.moodBefore === 'tired'}
                onClick={() => updateMovie({ moodBefore: currentMovie.moodBefore === 'tired' ? null : 'tired' })}
                icon={<BatteryLow className="w-4 h-4" />}
                label="Уставший"
              />
            </div>

            {/* Mood After */}
            <div className="flex gap-2 mb-3">
              <TagButton
                active={currentMovie.moodAfter === 'laughed'}
                onClick={() => updateMovie({ moodAfter: currentMovie.moodAfter === 'laughed' ? null : 'laughed' })}
                icon={<Laugh className="w-4 h-4" />}
                label="Угарал"
              />
              <TagButton
                active={currentMovie.moodAfter === 'cried'}
                onClick={() => updateMovie({ moodAfter: currentMovie.moodAfter === 'cried' ? null : 'cried' })}
                icon={<Frown className="w-4 h-4" />}
                label="Плакал"
              />
            </div>
          </div>

          {/* Custom Tags */}
          <div className="mt-6">
            <h3 className="text-sm font-medium text-muted-foreground mb-3">Свои теги</h3>
            <div className="flex flex-wrap gap-2">
              {currentMovie.customTags.map((tag, index) => (
                <span
                  key={index}
                  className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-muted rounded-full text-sm"
                >
                  {tag}
                  <button
                    onClick={() => handleRemoveTag(index)}
                    className="text-muted-foreground hover:text-foreground"
                  >
                    <X className="w-3.5 h-3.5" />
                  </button>
                </span>
              ))}
              {currentMovie.customTags.length < 5 && (
                <div className="flex items-center gap-1">
                  <input
                    type="text"
                    value={newTag}
                    onChange={(e) => setNewTag(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && handleAddTag()}
                    placeholder="Добавить тег..."
                    className="w-28 px-3 py-1.5 bg-muted rounded-full text-sm outline-none placeholder:text-muted-foreground"
                  />
                </div>
              )}
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex gap-3 mt-8">
            <button className="flex-1 flex items-center justify-center gap-2 py-3 bg-primary text-primary-foreground rounded-xl font-medium transition-transform active:scale-[0.98]">
              <UserPlus className="w-4 h-4" />
              Пригласить друзей
            </button>
            <button className="flex-1 flex items-center justify-center gap-2 py-3 bg-muted text-foreground rounded-xl font-medium transition-transform active:scale-[0.98]">
              <Send className="w-4 h-4" />
              Рекомендовать
            </button>
          </div>

          {/* Friend Ratings */}
          {currentMovie.friendRatings.length > 0 && (
            <div className="mt-10">
              <h3 className="text-sm font-medium text-muted-foreground mb-4">Друзья оценили</h3>
              <div className="flex flex-col gap-3">
                {currentMovie.friendRatings.map((friend) => (
                  <div key={friend.id} className="flex items-center gap-3">
                    <div className="relative w-10 h-10 rounded-full overflow-hidden">
                      <Image src={friend.avatar} alt={friend.name} fill className="object-cover" />
                    </div>
                    <span className="flex-1 text-foreground">{friend.name}</span>
                    <RatingBadge rating={friend.rating} size="md" />
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Best Rating */}
          {currentMovie.friendRatings.length > 0 && (
            <div className="mt-8 p-4 bg-muted/50 rounded-xl">
              <h3 className="text-sm font-medium text-muted-foreground mb-3">Лучшая оценка</h3>
              {(() => {
                const best = [...currentMovie.friendRatings].sort((a, b) => b.rating - a.rating)[0]
                return (
                  <div className="flex items-center gap-3">
                    <div className="relative w-12 h-12 rounded-full overflow-hidden">
                      <Image src={best.avatar} alt={best.name} fill className="object-cover" />
                    </div>
                    <span className="flex-1 font-medium text-foreground">{best.name}</span>
                    <RatingBadge rating={best.rating} size="lg" />
                  </div>
                )
              })()}
            </div>
          )}

          {/* Comments */}
          {currentMovie.comments.length > 0 && (
            <div className="mt-10 mb-8">
              <h3 className="text-sm font-medium text-muted-foreground mb-4">Комментарии</h3>
              <div className="flex flex-col gap-4">
                {currentMovie.comments.map((comment) => (
                  <div key={comment.id} className="flex gap-3">
                    <div className="relative w-9 h-9 rounded-full overflow-hidden flex-shrink-0">
                      <Image src={comment.avatar} alt={comment.userName} fill className="object-cover" />
                    </div>
                    <div className="flex-1">
                      <span className="text-sm font-medium text-foreground">{comment.userName}</span>
                      <p className="text-sm text-muted-foreground mt-0.5">{comment.text}</p>
                      <button className={cn(
                        'flex items-center gap-1 mt-2 text-xs',
                        comment.liked ? 'text-red-500' : 'text-muted-foreground'
                      )}>
                        <Heart className="w-3.5 h-3.5" fill={comment.liked ? 'currentColor' : 'none'} />
                        {comment.likes}
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </main>
    </div>
  )
}

function TagButton({ 
  active, 
  onClick, 
  icon, 
  label 
}: { 
  active: boolean
  onClick: () => void
  icon: React.ReactNode
  label: string 
}) {
  return (
    <button
      onClick={onClick}
      className={cn(
        'flex items-center gap-2 px-4 py-2 rounded-full text-sm transition-colors',
        active
          ? 'bg-primary text-primary-foreground'
          : 'bg-muted text-muted-foreground hover:text-foreground'
      )}
    >
      {icon}
      {label}
    </button>
  )
}
