'use client'

import { useState, useMemo } from 'react'
import Image from 'next/image'
import { Settings, Users, Film, BarChart3, TrendingUp, Calendar, Tag, Star } from 'lucide-react'
import { User, Movie } from '@/lib/types'
import { RatingBadge } from '@/components/rating-badge'

interface ProfileScreenProps {
  user: User
  onMovieClick: (movie: Movie) => void
  onSettings: () => void
}

type TabType = 'movies' | 'stats'

export function ProfileScreen({ user, onMovieClick, onSettings }: ProfileScreenProps) {
  const [activeTab, setActiveTab] = useState<TabType>('movies')

  const stats = useMemo(() => {
    const movies = user.movies
    if (movies.length === 0) return null

    // Average rating
    const avgRating = movies.reduce((sum, m) => sum + (m.rating || 0), 0) / movies.length

    // Year distribution
    const yearCounts: Record<number, number> = {}
    movies.forEach(m => {
      yearCounts[m.year] = (yearCounts[m.year] || 0) + 1
    })
    const yearDistribution = Object.entries(yearCounts)
      .map(([year, count]) => ({ year: parseInt(year), count }))
      .sort((a, b) => b.year - a.year)

    // Popular tags
    const tagCounts: Record<string, number> = {}
    movies.forEach(m => {
      m.customTags?.forEach(tag => {
        tagCounts[tag] = (tagCounts[tag] || 0) + 1
      })
    })
    const popularTags = Object.entries(tagCounts)
      .map(([tag, count]) => ({ tag, count }))
      .sort((a, b) => b.count - a.count)
      .slice(0, 6)

    // Rating distribution
    const ratingCounts: Record<number, number> = {}
    movies.forEach(m => {
      if (m.rating) {
        ratingCounts[m.rating] = (ratingCounts[m.rating] || 0) + 1
      }
    })
    const ratingDistribution = Array.from({ length: 10 }, (_, i) => ({
      rating: i + 1,
      count: ratingCounts[i + 1] || 0
    }))

    // Company distribution
    const companyCounts = { alone: 0, friends: 0, family: 0, date: 0 }
    movies.forEach(m => {
      if (m.company) {
        companyCounts[m.company] = (companyCounts[m.company] || 0) + 1
      }
    })

    // Mood stats
    const moodAfterCounts: Record<string, number> = {}
    movies.forEach(m => {
      if (m.moodAfter) {
        moodAfterCounts[m.moodAfter] = (moodAfterCounts[m.moodAfter] || 0) + 1
      }
    })

    // Best and worst movies
    const sortedByRating = [...movies].filter(m => m.rating).sort((a, b) => (b.rating || 0) - (a.rating || 0))
    const bestMovie = sortedByRating[0]
    const worstMovie = sortedByRating[sortedByRating.length - 1]

    return {
      totalMovies: movies.length,
      avgRating,
      yearDistribution,
      popularTags,
      ratingDistribution,
      companyCounts,
      moodAfterCounts,
      bestMovie,
      worstMovie,
    }
  }, [user.movies])

  const companyLabels: Record<string, string> = {
    alone: 'Один',
    friends: 'С друзьями',
    family: 'С семьёй',
    date: 'На свидании'
  }

  const moodLabels: Record<string, string> = {
    happy: 'Весёлый',
    sad: 'Грустный',
    tired: 'Уставший',
    excited: 'Взволнованный',
    cried: 'Плакал',
    laughed: 'Смеялся',
    bored: 'Скучал',
    inspired: 'Вдохновлён'
  }

  const getRatingColor = (rating: number) => {
    if (rating <= 3) return 'bg-red-500'
    if (rating <= 5) return 'bg-orange-500'
    if (rating <= 7) return 'bg-yellow-500'
    if (rating <= 8) return 'bg-lime-500'
    return 'bg-green-500'
  }

  return (
    <div className="min-h-screen bg-background">
      <header className="sticky top-0 z-10 bg-background/80 backdrop-blur-sm border-b border-border">
        <div className="max-w-md mx-auto px-4 py-3 flex items-center justify-between">
          <h1 className="text-xl font-semibold text-foreground">Профиль</h1>
          <button
            onClick={onSettings}
            className="w-10 h-10 rounded-full flex items-center justify-center hover:bg-muted transition-colors"
          >
            <Settings className="w-5 h-5 text-muted-foreground" />
          </button>
        </div>
      </header>

      <main className="max-w-md mx-auto px-4 py-6 pb-24">
        {/* Profile Header */}
        <div className="flex flex-col items-center text-center">
          <div className="relative w-24 h-24 rounded-full overflow-hidden ring-4 ring-muted">
            <Image
              src={user.avatar}
              alt={user.name}
              fill
              className="object-cover"
            />
          </div>
          <h2 className="text-xl font-semibold text-foreground mt-4">{user.name}</h2>
          <button className="flex items-center gap-2 mt-2 px-4 py-2 bg-muted rounded-full text-sm text-muted-foreground hover:text-foreground transition-colors">
            <Users className="w-4 h-4" />
            <span>{user.friendsCount} друзей</span>
          </button>
        </div>

        {/* Tabs */}
        <div className="flex items-center gap-2 mt-8 p-1 bg-muted rounded-full">
          <button
            onClick={() => setActiveTab('movies')}
            className={`flex-1 flex items-center justify-center gap-2 py-2.5 px-4 rounded-full text-sm font-medium transition-all ${
              activeTab === 'movies'
                ? 'bg-background text-foreground shadow-sm'
                : 'text-muted-foreground hover:text-foreground'
            }`}
          >
            <Film className="w-4 h-4" />
            <span>Фильмы</span>
          </button>
          <button
            onClick={() => setActiveTab('stats')}
            className={`flex-1 flex items-center justify-center gap-2 py-2.5 px-4 rounded-full text-sm font-medium transition-all ${
              activeTab === 'stats'
                ? 'bg-background text-foreground shadow-sm'
                : 'text-muted-foreground hover:text-foreground'
            }`}
          >
            <BarChart3 className="w-4 h-4" />
            <span>Статистика</span>
          </button>
        </div>

        {/* Movies Tab */}
        {activeTab === 'movies' && (
          <div className="mt-6">
            <div className="grid grid-cols-2 gap-3">
              {user.movies.map((movie) => (
                <button
                  key={movie.id}
                  onClick={() => onMovieClick(movie)}
                  className="relative aspect-[2/3] rounded-xl overflow-hidden bg-muted group"
                >
                  <Image
                    src={movie.poster}
                    alt={movie.title}
                    fill
                    className="object-cover transition-transform group-hover:scale-105"
                  />
                  {movie.rating && (
                    <div className="absolute bottom-2 right-2">
                      <RatingBadge rating={movie.rating} size="sm" />
                    </div>
                  )}
                  <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
                </button>
              ))}
            </div>

            {user.movies.length === 0 && (
              <div className="text-center py-12">
                <p className="text-muted-foreground">Ещё нет оценённых фильмов</p>
              </div>
            )}
          </div>
        )}

        {/* Stats Tab */}
        {activeTab === 'stats' && stats && (
          <div className="mt-6 space-y-6">
            {/* Main Stats */}
            <div className="grid grid-cols-2 gap-4">
              <div className="p-4 bg-muted/50 rounded-2xl">
                <div className="flex items-center gap-2 text-muted-foreground mb-2">
                  <Film className="w-4 h-4" />
                  <span className="text-xs">Всего фильмов</span>
                </div>
                <p className="text-3xl font-bold text-foreground">{stats.totalMovies}</p>
              </div>
              <div className="p-4 bg-muted/50 rounded-2xl">
                <div className="flex items-center gap-2 text-muted-foreground mb-2">
                  <Star className="w-4 h-4" />
                  <span className="text-xs">Средняя оценка</span>
                </div>
                <p className="text-3xl font-bold text-foreground">{stats.avgRating.toFixed(1)}</p>
              </div>
            </div>

            {/* Rating Distribution */}
            <div className="p-4 bg-muted/50 rounded-2xl">
              <div className="flex items-center gap-2 text-muted-foreground mb-4">
                <TrendingUp className="w-4 h-4" />
                <span className="text-sm font-medium">Распределение оценок</span>
              </div>
              <div className="flex items-end justify-between gap-1 h-24">
                {stats.ratingDistribution.map(({ rating, count }) => {
                  const maxCount = Math.max(...stats.ratingDistribution.map(r => r.count))
                  const height = maxCount > 0 ? (count / maxCount) * 100 : 0
                  return (
                    <div key={rating} className="flex-1 flex flex-col items-center gap-1">
                      <div
                        className={`w-full rounded-t-sm transition-all ${getRatingColor(rating)} ${count === 0 ? 'opacity-20' : ''}`}
                        style={{ height: `${Math.max(height, 4)}%` }}
                      />
                      <span className="text-[10px] text-muted-foreground">{rating}</span>
                    </div>
                  )
                })}
              </div>
            </div>

            {/* Year Distribution */}
            <div className="p-4 bg-muted/50 rounded-2xl">
              <div className="flex items-center gap-2 text-muted-foreground mb-4">
                <Calendar className="w-4 h-4" />
                <span className="text-sm font-medium">По годам выпуска</span>
              </div>
              <div className="space-y-2">
                {stats.yearDistribution.slice(0, 5).map(({ year, count }) => {
                  const maxCount = Math.max(...stats.yearDistribution.map(y => y.count))
                  const width = (count / maxCount) * 100
                  return (
                    <div key={year} className="flex items-center gap-3">
                      <span className="text-sm text-muted-foreground w-12">{year}</span>
                      <div className="flex-1 h-6 bg-muted rounded-full overflow-hidden">
                        <div
                          className="h-full bg-accent rounded-full transition-all"
                          style={{ width: `${width}%` }}
                        />
                      </div>
                      <span className="text-sm font-medium text-foreground w-6 text-right">{count}</span>
                    </div>
                  )
                })}
              </div>
            </div>

            {/* Popular Tags */}
            {stats.popularTags.length > 0 && (
              <div className="p-4 bg-muted/50 rounded-2xl">
                <div className="flex items-center gap-2 text-muted-foreground mb-4">
                  <Tag className="w-4 h-4" />
                  <span className="text-sm font-medium">Популярные теги</span>
                </div>
                <div className="flex flex-wrap gap-2">
                  {stats.popularTags.map(({ tag, count }) => (
                    <span
                      key={tag}
                      className="px-3 py-1.5 bg-background rounded-full text-sm text-foreground"
                    >
                      {tag} <span className="text-muted-foreground">({count})</span>
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Company Stats */}
            <div className="p-4 bg-muted/50 rounded-2xl">
              <div className="flex items-center gap-2 text-muted-foreground mb-4">
                <Users className="w-4 h-4" />
                <span className="text-sm font-medium">С кем смотрю</span>
              </div>
              <div className="grid grid-cols-2 gap-3">
                {Object.entries(stats.companyCounts).map(([company, count]) => (
                  count > 0 && (
                    <div key={company} className="flex items-center justify-between p-2 bg-background rounded-lg">
                      <span className="text-sm text-muted-foreground">{companyLabels[company]}</span>
                      <span className="text-sm font-medium text-foreground">{count}</span>
                    </div>
                  )
                ))}
              </div>
            </div>

            {/* Mood After Stats */}
            {Object.keys(stats.moodAfterCounts).length > 0 && (
              <div className="p-4 bg-muted/50 rounded-2xl">
                <div className="flex items-center gap-2 text-muted-foreground mb-4">
                  <span className="text-sm font-medium">Настроение после просмотра</span>
                </div>
                <div className="flex flex-wrap gap-2">
                  {Object.entries(stats.moodAfterCounts).map(([mood, count]) => (
                    <span
                      key={mood}
                      className="px-3 py-1.5 bg-background rounded-full text-sm text-foreground"
                    >
                      {moodLabels[mood] || mood} <span className="text-muted-foreground">({count})</span>
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Best & Worst */}
            {stats.bestMovie && stats.worstMovie && stats.bestMovie.id !== stats.worstMovie.id && (
              <div className="grid grid-cols-2 gap-4">
                <div className="p-4 bg-green-500/10 rounded-2xl">
                  <p className="text-xs text-green-600 mb-2">Лучший фильм</p>
                  <p className="text-sm font-medium text-foreground truncate">{stats.bestMovie.title}</p>
                  <p className="text-2xl font-bold text-green-600 mt-1">{stats.bestMovie.rating}</p>
                </div>
                <div className="p-4 bg-red-500/10 rounded-2xl">
                  <p className="text-xs text-red-600 mb-2">Худший фильм</p>
                  <p className="text-sm font-medium text-foreground truncate">{stats.worstMovie.title}</p>
                  <p className="text-2xl font-bold text-red-600 mt-1">{stats.worstMovie.rating}</p>
                </div>
              </div>
            )}
          </div>
        )}

        {activeTab === 'stats' && !stats && (
          <div className="text-center py-12 mt-6">
            <p className="text-muted-foreground">Добавьте фильмы, чтобы увидеть статистику</p>
          </div>
        )}
      </main>
    </div>
  )
}
