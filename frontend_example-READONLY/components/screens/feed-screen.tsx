'use client'

import { Plus } from 'lucide-react'
import { Movie } from '@/lib/types'
import { MovieCard } from '@/components/movie-card'

interface FeedScreenProps {
  movies: Movie[]
  onMovieClick: (movie: Movie) => void
  onAddMovie: () => void
}

export function FeedScreen({ movies, onMovieClick, onAddMovie }: FeedScreenProps) {
  return (
    <div className="min-h-screen bg-background">
      <header className="sticky top-0 z-10 bg-background/80 backdrop-blur-sm border-b border-border">
        <div className="max-w-md mx-auto px-4 py-4 flex items-center justify-between">
          <h1 className="text-xl font-semibold text-foreground">Двойной вкус</h1>
          <button
            onClick={onAddMovie}
            className="w-10 h-10 rounded-full bg-primary text-primary-foreground flex items-center justify-center transition-transform active:scale-95"
          >
            <Plus className="w-5 h-5" />
          </button>
        </div>
      </header>
      
      <main className="max-w-md mx-auto px-4 py-4 pb-24">
        <div className="flex flex-col gap-3">
          {movies.map((movie) => (
            <MovieCard
              key={movie.id}
              movie={movie}
              onClick={() => onMovieClick(movie)}
            />
          ))}
        </div>
        
        {movies.length === 0 && (
          <div className="text-center py-20">
            <p className="text-muted-foreground">Пока нет оценённых фильмов</p>
            <button
              onClick={onAddMovie}
              className="mt-4 text-primary font-medium"
            >
              Добавить первый фильм
            </button>
          </div>
        )}
      </main>
    </div>
  )
}
