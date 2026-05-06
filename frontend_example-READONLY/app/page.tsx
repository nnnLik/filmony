'use client'

import { useState } from 'react'
import { Movie } from '@/lib/types'
import { mockMovies, currentUser } from '@/lib/mock-data'
import { BottomNav } from '@/components/bottom-nav'
import { FeedScreen } from '@/components/screens/feed-screen'
import { MovieDetailScreen } from '@/components/screens/movie-detail-screen'
import { ProfileScreen } from '@/components/screens/profile-screen'
import { SearchScreen } from '@/components/screens/search-screen'
import { AddMovieScreen } from '@/components/screens/add-movie-screen'

type Tab = 'feed' | 'search' | 'profile'
type Screen = 'main' | 'movie-detail' | 'add-movie' | 'settings'

export default function DoubleTastePage() {
  const [activeTab, setActiveTab] = useState<Tab>('feed')
  const [currentScreen, setCurrentScreen] = useState<Screen>('main')
  const [selectedMovie, setSelectedMovie] = useState<Movie | null>(null)
  const [movies, setMovies] = useState<Movie[]>(mockMovies)

  const handleMovieClick = (movie: Movie) => {
    setSelectedMovie(movie)
    setCurrentScreen('movie-detail')
  }

  const handleBack = () => {
    setCurrentScreen('main')
    setSelectedMovie(null)
  }

  const handleAddMovie = () => {
    setCurrentScreen('add-movie')
  }

  const handleMovieUpdate = (updatedMovie: Movie) => {
    setMovies(movies.map(m => m.id === updatedMovie.id ? updatedMovie : m))
    setSelectedMovie(updatedMovie)
  }

  const handleNewMovie = (newMovie: Movie) => {
    setMovies([newMovie, ...movies])
    setSelectedMovie(newMovie)
    setCurrentScreen('movie-detail')
  }

  const handleSettings = () => {
    // Settings screen placeholder
    console.log('Settings clicked')
  }

  // Render current screen
  if (currentScreen === 'movie-detail' && selectedMovie) {
    return (
      <MovieDetailScreen
        movie={selectedMovie}
        onBack={handleBack}
        onUpdate={handleMovieUpdate}
      />
    )
  }

  if (currentScreen === 'add-movie') {
    return (
      <AddMovieScreen
        onBack={handleBack}
        onAdd={handleNewMovie}
      />
    )
  }

  return (
    <div className="min-h-screen bg-background">
      {activeTab === 'feed' && (
        <FeedScreen
          movies={movies}
          onMovieClick={handleMovieClick}
          onAddMovie={handleAddMovie}
        />
      )}

      {activeTab === 'search' && (
        <SearchScreen
          movies={movies}
          onMovieClick={handleMovieClick}
        />
      )}

      {activeTab === 'profile' && (
        <ProfileScreen
          user={{ ...currentUser, movies }}
          onMovieClick={handleMovieClick}
          onSettings={handleSettings}
        />
      )}

      <BottomNav activeTab={activeTab} onTabChange={setActiveTab} />
    </div>
  )
}
