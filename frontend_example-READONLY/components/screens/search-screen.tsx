'use client'

import { useState } from 'react'
import Image from 'next/image'
import { Search } from 'lucide-react'
import { Movie } from '@/lib/types'
import { RatingBadge } from '@/components/rating-badge'

interface SearchScreenProps {
  movies: Movie[]
  onMovieClick: (movie: Movie) => void
}

export function SearchScreen({ movies, onMovieClick }: SearchScreenProps) {
  const [query, setQuery] = useState('')

  const filteredMovies = movies.filter((movie) =>
    movie.title.toLowerCase().includes(query.toLowerCase())
  )

  return (
    <div className="min-h-screen bg-background">
      <header className="sticky top-0 z-10 bg-background/80 backdrop-blur-sm border-b border-border">
        <div className="max-w-md mx-auto px-4 py-3">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-muted-foreground" />
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Поиск фильмов..."
              className="w-full pl-10 pr-4 py-3 bg-muted rounded-xl text-foreground placeholder:text-muted-foreground outline-none focus:ring-2 focus:ring-primary/20"
            />
          </div>
        </div>
      </header>

      <main className="max-w-md mx-auto px-4 py-4 pb-24">
        {query.length === 0 ? (
          <div className="text-center py-20">
            <Search className="w-12 h-12 text-muted-foreground/50 mx-auto mb-4" />
            <p className="text-muted-foreground">Начните вводить название фильма</p>
          </div>
        ) : filteredMovies.length === 0 ? (
          <div className="text-center py-20">
            <p className="text-muted-foreground">Ничего не найдено</p>
          </div>
        ) : (
          <div className="flex flex-col gap-2">
            {filteredMovies.map((movie) => (
              <button
                key={movie.id}
                onClick={() => onMovieClick(movie)}
                className="flex items-center gap-3 p-3 rounded-xl hover:bg-muted transition-colors text-left"
              >
                <div className="relative w-12 h-16 rounded-lg overflow-hidden flex-shrink-0 bg-muted">
                  <Image
                    src={movie.poster}
                    alt={movie.title}
                    fill
                    className="object-cover"
                  />
                </div>
                <div className="flex-1 min-w-0">
                  <h3 className="font-medium text-foreground truncate">{movie.title}</h3>
                  <p className="text-sm text-muted-foreground">{movie.year}</p>
                </div>
                {movie.rating && <RatingBadge rating={movie.rating} size="md" />}
              </button>
            ))}
          </div>
        )}
      </main>
    </div>
  )
}
