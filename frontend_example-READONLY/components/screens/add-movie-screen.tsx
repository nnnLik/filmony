'use client'

import { useState } from 'react'
import Image from 'next/image'
import { ArrowLeft, Link as LinkIcon, Film, Loader2 } from 'lucide-react'
import { Movie } from '@/lib/types'

interface AddMovieScreenProps {
  onBack: () => void
  onAdd: (movie: Movie) => void
}

// Simulated movie data for demo
const demoMovies: Record<string, { title: string; year: number; poster: string }> = {
  'kinopoisk': {
    title: 'Интерстеллар',
    year: 2014,
    poster: 'https://images.unsplash.com/photo-1419242902214-272b3f66ee7a?w=300&h=450&fit=crop',
  },
}

export function AddMovieScreen({ onBack, onAdd }: AddMovieScreenProps) {
  const [link, setLink] = useState('')
  const [loading, setLoading] = useState(false)
  const [preview, setPreview] = useState<{ title: string; year: number; poster: string } | null>(null)

  const handleLinkChange = (value: string) => {
    setLink(value)
    if (value.includes('kinopoisk')) {
      setLoading(true)
      // Simulate API call
      setTimeout(() => {
        setPreview(demoMovies['kinopoisk'])
        setLoading(false)
      }, 800)
    } else {
      setPreview(null)
    }
  }

  const handleCreate = () => {
    if (preview) {
      const newMovie: Movie = {
        id: Date.now().toString(),
        title: preview.title,
        year: preview.year,
        poster: preview.poster,
        rating: null,
        company: null,
        moodBefore: null,
        moodAfter: null,
        customTags: [],
        friendRatings: [],
        comments: [],
      }
      onAdd(newMovie)
    }
  }

  return (
    <div className="min-h-screen bg-background">
      <header className="sticky top-0 z-10 bg-background/80 backdrop-blur-sm border-b border-border">
        <div className="max-w-md mx-auto px-4 py-3 flex items-center gap-3">
          <button
            onClick={onBack}
            className="w-10 h-10 rounded-full flex items-center justify-center hover:bg-muted transition-colors"
          >
            <ArrowLeft className="w-5 h-5" />
          </button>
          <h1 className="font-medium text-foreground">Добавить фильм</h1>
        </div>
      </header>

      <main className="max-w-md mx-auto px-4 py-6">
        <div className="flex flex-col gap-6">
          {/* Link Input */}
          <div>
            <label className="text-sm font-medium text-muted-foreground mb-2 block">
              Ссылка на Кинопоиск
            </label>
            <div className="relative">
              <LinkIcon className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-muted-foreground" />
              <input
                type="url"
                value={link}
                onChange={(e) => handleLinkChange(e.target.value)}
                placeholder="https://www.kinopoisk.ru/film/..."
                className="w-full pl-12 pr-4 py-4 bg-muted rounded-xl text-foreground placeholder:text-muted-foreground outline-none focus:ring-2 focus:ring-primary/20"
              />
            </div>
            <p className="text-xs text-muted-foreground mt-2">
              Вставьте ссылку на фильм с Кинопоиска для автоматического заполнения
            </p>
          </div>

          {/* Loading */}
          {loading && (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="w-8 h-8 text-primary animate-spin" />
            </div>
          )}

          {/* Preview */}
          {preview && !loading && (
            <div className="bg-muted/50 rounded-xl p-4">
              <div className="flex gap-4">
                <div className="relative w-24 h-36 rounded-lg overflow-hidden flex-shrink-0 bg-muted">
                  <Image
                    src={preview.poster}
                    alt={preview.title}
                    fill
                    className="object-cover"
                  />
                </div>
                <div className="flex flex-col justify-center">
                  <h3 className="font-semibold text-foreground text-lg">{preview.title}</h3>
                  <p className="text-muted-foreground">{preview.year}</p>
                </div>
              </div>
            </div>
          )}

          {/* Empty State */}
          {!preview && !loading && !link && (
            <div className="text-center py-12">
              <div className="w-16 h-16 bg-muted rounded-full flex items-center justify-center mx-auto mb-4">
                <Film className="w-8 h-8 text-muted-foreground" />
              </div>
              <p className="text-muted-foreground">
                Вставьте ссылку для предпросмотра
              </p>
            </div>
          )}

          {/* Create Button */}
          <button
            onClick={handleCreate}
            disabled={!preview || loading}
            className="w-full py-4 bg-primary text-primary-foreground rounded-xl font-medium disabled:opacity-50 disabled:cursor-not-allowed transition-all active:scale-[0.98]"
          >
            Создать карточку
          </button>
        </div>
      </main>
    </div>
  )
}
